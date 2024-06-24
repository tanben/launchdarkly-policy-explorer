from dotenv import load_dotenv
import os


class AppConfig:
    def __init__(self):
        load_dotenv()

        self.access_token = os.getenv("LAUNCHDARKLY_API_KEY")
        self.debug = os.getenv("DEBUG",'False').lower()  == 'true'
        self.save_data =os.getenv("SAVE_DATA",'False').lower()  == 'true'
        self.read_local = os.getenv("READ_LOCAL",'False').lower() == 'true'
        self.output_dir = os.getenv("OUTPUT_DIR",'output')

    def __str__(self) -> str:
        return f"access_token={self.access_token}, debug={self.debug}, save_data={self.save_data}, read_local={self.read_local}, output_dir={self.output_dir}"
