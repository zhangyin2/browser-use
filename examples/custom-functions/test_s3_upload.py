import asyncio
import os
from pathlib import Path

from langchain_openai import ChatOpenAI

from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig

# S3 configuration - required for security/isolation
USER_ID = 'test_user_123'  # This will be part of your S3 path
S3_BUCKET = 'your-test-bucket'  # Replace with your actual bucket name
S3_FILE_PATH = f's3://{S3_BUCKET}/users/{USER_ID}/test_file.txt'

# Initialize browser
browser = Browser(
	config=BrowserConfig(
		headless=False,
		chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
	)
)

# For S3 uploads, we need user_id and s3_user_prefix for security
# This ensures users can only access their own files in S3
controller = Controller(
	user_id=USER_ID,  # Required for S3 security
	s3_user_prefix=f'users/{USER_ID}/',  # Restricts S3 access to user's directory
)


async def main():
	# Verify S3 file exists before running test
	import boto3

	s3 = boto3.client('s3')
	try:
		# Check if file exists
		s3.head_object(Bucket=S3_BUCKET, Key=f'users/{USER_ID}/test_file.txt')
	except Exception as e:
		print(f'Error: S3 file not found. Please make sure file exists at {S3_FILE_PATH}')
		print('You can create it using:')
		print(f'aws s3 cp test_file.txt s3://{S3_BUCKET}/users/{USER_ID}/test_file.txt')
		exit(1)

	# For S3 upload test, we'll use the same httpbin form
	task = f"""
    1.  Go togo to https://kzmpmkh2zfk1ojnpxfn1.lite.vusercontent.net/ and upload to each upload field my file
    2. Upload the file from S3 at {S3_FILE_PATH}
    """

	model = ChatOpenAI(model='gpt-4o')
	agent = Agent(
		task=task,
		llm=model,
		controller=controller,
		browser=browser,
	)

	try:
		await agent.run()
	finally:
		await browser.close()


if __name__ == '__main__':
	# Make sure AWS credentials are set in environment
	if not all([os.getenv('AWS_ACCESS_KEY_ID'), os.getenv('AWS_SECRET_ACCESS_KEY')]):
		print('Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables')
		exit(1)

	asyncio.run(main())
