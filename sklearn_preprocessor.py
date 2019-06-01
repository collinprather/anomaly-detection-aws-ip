from __future__ import print_function

import time
import sys
from io import StringIO
import os
import shutil

import argparse
import csv
import json
import numpy as np
import pandas as pd

from sklearn.externals import joblib
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Binarizer, StandardScaler

from sagemaker_containers.beta.framework import (
    content_types, encoders, env, modules, transformer, worker)

# Since we get a headerless CSV file we specify the column names here.
feature_columns_names = ['timestamp', 'value']

feature_columns_dtype = {'timestamp': str, 'value': np.float64}


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    # Sagemaker specific arguments. Defaults are set in the environment variables.
    parser.add_argument('--output-data-dir', type=str, default=os.environ['SM_OUTPUT_DATA_DIR'])
    parser.add_argument('--model-dir', type=str, default=os.environ['SM_MODEL_DIR'])
    parser.add_argument('--train', type=str, default=os.environ['SM_CHANNEL_TRAIN'])

    args = parser.parse_args()

    # Take the set of files and read them all into a single pandas dataframe
    input_files = [ os.path.join(args.train, file) for file in os.listdir(args.train) ]
    if len(input_files) == 0:
        raise ValueError(('There are no files in {}.\n' +
                          'This usually indicates that the channel ({}) was incorrectly specified,\n' +
                          'the data specification in S3 was incorrectly specified or the role specified\n' +
                          'does not have permission to access the data.').format(args.train, "train"))
    
    # we can add names = feature_columns_names argument to pd.read_csv, if input data has no header
    raw_data = [ pd.read_csv(file, dtype = feature_columns_dtype, index_col = 0, 
                             parse_dates = True) for file in input_files ]
    
    # notice here that default axis=0, so the data is concatenated vertically
    concat_data = pd.concat(raw_data)
    
    # Create actual pre-processing pipeline
    preprocessor = make_pipeline(StandardScaler())
    preprocessor.fit(concat_data)
    
    joblib.dump(preprocessor, os.path.join(args.model_dir, "model.joblib"))

    print("saved model!")
    
    
    
def input_fn(input_data, content_type):
    """Parse input data payload

    Basically reads the data into a pd.DataFrame.
    Checks to make sure it is csv file
    """
    if content_type == 'text/csv':
        # Read the raw input data as CSV.
        df = pd.read_csv(StringIO(input_data), index_col = 0, parse_dates = True, header = None)
        #df.columns = feature_columns_names

        return df
    else:
        raise ValueError("{} not supported by script!".format(content_type))

        
def output_fn(prediction, accept):
    """Format prediction output

    The default accept/content-type between containers for serial inference is JSON.
    We also want to set the ContentType or mimetype as the same value as accept so the next
    container can read the response payload correctly.
    """
    if accept == "application/json":
        instances = []
        for row in prediction.tolist():
            instances.append({"features": row})

        json_output = {"instances": instances}

        return worker.Response(json.dumps(json_output), accept, mimetype=accept)
    elif accept == 'text/csv':
        return worker.Response(encoders.encode(prediction, accept), accept, mimetype=accept)
    else:
        raise RuntimeException("{} accept type is not supported by this script.".format(accept))


def predict_fn(input_data, model):
    """Preprocess input data

    We implement this because the default predict_fn uses .predict(), but our model is a preprocessor
    so we want to use .transform().

    The output returned is the standardized features
    """
    features = model.transform(input_data)

    return features


def model_fn(model_dir):
    """Deserialize fitted model
    """
    preprocessor = joblib.load(os.path.join(model_dir, "model.joblib"))
    return preprocessor
    
    