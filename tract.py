from flask import Flask, jsonify, request
import boto3
import os
import uuid;
os.environ['AWS_ACCESS_KEY_ID'] = ''
os.environ['AWS_SECRET_ACCESS_KEY'] = ''
os.environ['AWS_DEFAULT_REGION'] = 'ap-south-1'
app = Flask(__name__)
S3_BUCKET = 'mobile-app-textract'
S3_ACCESS_KEY = ''
S3_SECRET_KEY = ''
S3_REGION = 'ap-south-1'
# Initialize Textract client
def initialize_textract_client():
     return boto3.client('textract')

s3 = boto3.client(
    's3',
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION
)

# def load_image_from_path(file_name):
#     try:
#         textract_client = initialize_textract_client()
#         with open(file_name, 'rb') as file:
#             image_bytes = textract_client.analyze_document(
#                 Document={
                    
#                     'Bytes': file.read(),
#                 },
#                 FeatureTypes=["FORMS","TABLES"])
#         return image_bytes
#     except Exception as e:
#         return None
    
def detect_text(image_bytes):
    try:
        textract_client = initialize_textract_client()
        response = textract_client.analyze_document(
            Document={'Bytes': image_bytes},
            FeatureTypes=["TABLES", "FORMS"]
        )
        return response
    except Exception as e:
        return {'error': str(e)}

def extract_text_by_block_type(response, block_type):
    word_map={}
    for item in response['Blocks']:
        if item['BlockType'] == block_type:
            word_map[item["Id"]]=item["Text"]
        if item['BlockType']=="SELECTION_ELEMENT":
            word_map[item["Id"]]=item["SelectionStatus"]
    return word_map
def extract_table_info(response, word_map):
    row = []
    table = {}
    ri = 0
    flag = False

    for block in response["Blocks"]:
        if block["BlockType"] == "TABLE":
            key = f"table_{uuid.uuid4().hex}"
            table_n = +1
            temp_table = []

        if block["BlockType"] == "CELL":
            if block["RowIndex"] != ri:
                flag = True
                row = []
                ri = block["RowIndex"]

            if "Relationships" in block:
                for relation in block["Relationships"]:
                    if relation["Type"] == "CHILD":
                        row.append(" ".join([word_map[i] for i in relation["Ids"]]))
            else:
                row.append(" ")

            if flag:
                temp_table.append(row)
                table[key] = temp_table
                flag = False
    return table

@app.route('/table_textract_text', methods=['POST'])
def read_text():
    data = request.get_json()
    file_name = data.get('file_name', None)
        
    if not file_name:
        return jsonify({'message': 'Image path not provided'})
    try:
        # Load image from path
        s3_bucket_name = 'mobile-app-textract'
        s3_key = data['file_name']  # Update with your S3 image key
        s3_client = boto3.client('s3')
        image_object = s3_client.get_object(Bucket=s3_bucket_name, Key=s3_key)
        image_bytes = image_object['Body'].read()

        # Detect text in the image
        
        # image_bytes = load_image_from_path(file_name)
        # print(image_bytes)
        
        
        response = detect_text(image_bytes)
        print(response)
        
        if 'error' in response:
            return jsonify({'message': 'Text detection failed'})
        
        block_type = 'WORD'
        extracted_text = extract_text_by_block_type(response, block_type)
        # print(extracted_text)
        extracted_table=extract_table_info(response,extracted_text )
        # print(extracted_table)
        
        return jsonify({'message': 'Text extracted successfully', 'text': extracted_table})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0')
