import os
from notion_client import Client
from django.http import HttpResponse
from dotenv import load_dotenv
from xhtml2pdf import pisa
from django.template.loader import get_template
from datetime import datetime
from django.conf import settings

# Load .env file for API keys
load_dotenv()

# Set up Notion API client
notion = Client(auth=os.getenv('NOTION_TOKEN'))
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

def get_notion_todos():
    """
    Fetch the list of to-do items from the Notion database using notion-client.
    """
    try:
        response = notion.blocks.children.list(block_id=NOTION_DATABASE_ID)
        page = notion.pages.retrieve(NOTION_DATABASE_ID)
        title = page['properties']['title']['title'][0]['text']['content']
        
        return [response,title]
    except Exception as e:
        print(f"Error fetching to-dos from Notion: {e}")
        return None

def parse_todos(todos_data):
    structured_data = []
    current_module = None
    cours_count=0

    for item in todos_data['results']:
        if item['type'] == 'heading_1':
            current_module = {
                'title': item['heading_1']['rich_text'][0]['text']['content'],
                'submodules': []
            }
            structured_data.append(current_module)

        elif item['type'] == 'to_do':
            if current_module:  # Ensure we are within a submodule
                if item['to_do']['checked']:
                    cours_count+=1
                    todo_item = item['to_do']['rich_text'][0]['text']['content']
                    current_module['todos'].append(todo_item)

    return [structured_data,cours_count]

def render_pdf_view(request):
    """
    Generate a PDF from the to-do list fetched from Notion.
    """
    todos_data = get_notion_todos()  
    pdf_file_path = os.path.join(settings.MEDIA_ROOT, 'todo_list.pdf')

    if todos_data:
        modules = parse_todos(todos_data[0])  # Parse the todo data to structure it
        update_time = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
        course_count = modules[1]  # Count of courses/items

        template = get_template('todo_pdf.html')
        html = template.render({'structured_data': modules[0], 'title': todos_data[1], 'update_time': update_time, 'course_count': course_count})

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="todo_list.pdf"'  # Display in browser
        


        # Create PDF

        with open(pdf_file_path, 'w+b') as pdf_file:
            pisa_status = pisa.CreatePDF(html, dest=pdf_file)

            if pisa_status.err:
                return HttpResponse('Error generating PDF', status=500)
            
            # Optionally return the PDF in response as well
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="todo_list.pdf"'  # Display in browser
            pdf_file.seek(0)  # Go back to the start of the file
            response.write(pdf_file.read())  # Write the PDF data to response

    else:
    # If todos_data is empty, check if the PDF file exists and serve it
        if os.path.exists(pdf_file_path):
            with open(pdf_file_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="todo_list.pdf"'  # Display in browser
                return response
        else:
            return HttpResponse('No to-do data and no previous PDF available.', status=404)
    return response


