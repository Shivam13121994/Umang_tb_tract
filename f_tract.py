
import boto3
import os
from flask import Flask, request, jsonify
os.environ['AWS_ACCESS_KEY_ID'] = ''
os.environ['AWS_SECRET_ACCESS_KEY'] = ''
os.environ['AWS_DEFAULT_REGION'] = 'ap-south-1'

app = Flask(__name__)
S3_BUCKET = 'mobile-app-textract'
S3_ACCESS_KEY = ''
S3_SECRET_KEY = ''
S3_REGION = 'ap-south-1'

# Create an S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION
)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        data = request.get_json()

        if 'file_path' not in data:
            return jsonify({'error': 'File path not provided'}), 400

        file_path = data['file_path']

        if not os.path.isfile(file_path):
            return jsonify({'error': 'File not found at the provided path'}), 400

        # Extract file name from the provided path
        filename = os.path.basename(file_path)

        # Open the file
        with open(file_path, 'rb') as file:
            # Upload the file to S3
            s3.upload_fileobj(
                file,
                S3_BUCKET,
                filename,
            )

            # Generate the URL for the uploaded file
            file_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"

            return jsonify({'success': True, 'file_url': file_url}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize Textract client
def initialize_textract_client():
    return boto3.client('textract')

# Function to detect text in an image
def detect_text(image_bytes):
    try:
        textract_client = initialize_textract_client()
        response = textract_client.detect_document_text(Document={'Bytes': image_bytes})
        return response
    except Exception as e:
        return {'error': str(e)}

def extract_text_by_block_type(response, block_type):
    extracted_text = ""
    for item in response['Blocks']:
        if item['BlockType'] == block_type:
            extracted_text += item['Text'] + " "
    return extracted_text.strip()

@app.route('/textract_text', methods=['POST'])
def read_text():
    data = request.get_json()
    # file_name=os.path.basename(file_path)
    if 'file_name' not in data:
        return jsonify({'error': 'File name not provided'}), 400
    try:
        # Retrieve uploaded image from S3
        s3_bucket_name = 'mobile-app-textract'
        s3_key = data['file_name']  # Update with your S3 image key
        s3_client = boto3.client('s3')
        image_object = s3_client.get_object(Bucket=s3_bucket_name, Key=s3_key)
        image_bytes = image_object['Body'].read()

        # Detect text in the image
        response = detect_text(image_bytes)
        
        if 'error' in response:
            return jsonify({'message': 'Text detection failed'})

        block_type = 'WORD'
        extracted_text = extract_text_by_block_type(response, block_type)

        return jsonify({'message': 'Text extracted successfully', 'text': extracted_text})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
   
    app.run(host='0.0.0.0')
