from django.test import TestCase
from notion_client import Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NotionTestCase(TestCase):
    def setUp(self):
        """
        Set up the Notion client with the API token and database ID.
        """
        self.notion = Client(auth=os.getenv('NOTION_TOKEN'))
        self.database_id = os.getenv('NOTION_DATABASE_ID')

    def test_notion_database_access(self):
        """
        Test if the Notion database is accessible and returns valid data.
        """
        try:
            response = self.notion.databases.query(database_id=self.database_id)
            self.assertTrue(len(response['results']) > 0, "No data found in the database.")
        except Exception as e:
            self.fail(f"Failed to fetch data from Notion: {e}")
