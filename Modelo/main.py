from dotenv import load_dotenv

from web_app import WebApp

load_dotenv()


if __name__ == '__main__':
    web_app = WebApp()
    web_app.run()
