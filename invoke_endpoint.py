import boto3

client = boto3.client('sagemaker-runtime')

custom_attributes = "c000b4f9-df62-4c85-a0bf-7c525f9104a4"  # An example of a trace ID.
endpoint_name = "sample-anomaly-endpoint"                   # Your endpoint name.
content_type = "text/csv"                                   # The MIME type of the input data in the request body.
accept = "text/csv"                                         # The desired MIME type of the inference in the response.
payload = "2013-12-02 21:15:00, 75"                         # Payload for inference.



response = client.invoke_endpoint(
    EndpointName=endpoint_name,
    CustomAttributes=custom_attributes,  
    ContentType=content_type,
    Accept=accept,
    Body=payload
    )



print('\nThe payload recevied an anomaly score of {}.\n'.format(response['Body'].read()))
# The payload recevied an anomaly score of b'{scores:[{score:0.90694374}]}'.