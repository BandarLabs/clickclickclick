# ClickClickClick on Raspberry Pi Zero 2W

![raspberry pi](https://github.com/user-attachments/assets/da020494-d167-40da-839f-fa2cb4442002)

You can now control your phones using a raspberry pi and talking to it

```python
click3 run "Can you open Gmail and draft this email"
```

```python
click3 run "Can you check bus stops in Nashville"
```


ClickClickClick framework on a Raspberry Pi Zero 2W.

## Prerequisites

1. **Operating System**: Ensure your Raspberry Pi Zero 2W is running a version of Raspbian that supports Python 3.11.
2. **Python**: Install Python 3.11 or higher.
   ```sh
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3.11-dev
   ```
3. **PIP**: Might be already installed.
   ```sh
   curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.11
   ```

## Install Dependencies

1. **ADB**: It might be already installed.
   ```sh
   sudo apt install adb
   ```



## Install the ClickClickClick Package

### Using pip

You can directly install the latest version of ClickClickClick from the GitHub repository.

```sh
python3.11 -m pip install git+https://github.com/instavm/clickclickclick.git
```



## Configuration

 **API Keys**: Set up the required API keys for OpenAI (optional) and Gemini.

   ```sh
   export OPENAI_API_KEY=your_openai_api_key
   export GEMINI_API_KEY=your_gemini_api_key
   ```


## Running the tool

### From a CLI

Use the `click3` command line tool to run tasks.

```sh
click3 run "Open uber app"
```

### As a Web Interface

Start the Gradio web interface.

```sh
click3 gradio
```

![gradio-ui](https://github.com/user-attachments/assets/610540f3-d324-4b6a-af9f-14e275f3b520)

## Troubleshooting

If you encounter any issues during the installation or the running of the ClickClickClick framework, please refer to the main repository's documentation or create an issue on the GitHub page.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
