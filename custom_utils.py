import json
import os


class Utils:

    def read_json_file(file_path: str):

        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            print(f"Error: File not found at '{file_path}'")
            return None
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in '{file_path}'")
            return None

    def save_data_to_file(data: dict, filename: str):

        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Data saved successfully to {filename}")
        except Exception as e:
            print(f"Error saving data to file: {e}")

    def print_json(input: dict):
        print(json.dumps(input, indent=4))


def main():
    file_path = "./output/roles.json"  # Replace with your JSON file path
    data = Utils.read_json_file(file_path)

    if data is None:
        return data

    print("Loaded data:", data)
    print(len(data))
    for item in data:
        print(item['key'])


if __name__ == '__main__':
    main()
