import requests
import markdown
import re
import random
import keyring

token = keyring.get_password('github', 'token')
owner = keyring.get_password('github', 'username')
repo = "Vault"


def get_api_response(path: str) -> dict:
    """Send request to Github repo to get the files from the requested root folder."""

    response = requests.get(
        f'https://api.github.com/repos/{owner}/{repo}/contents/{path}',
        headers={
            'accept': 'application/vnd.github.v3.raw',
            'authorization': f'token {token}'
        }
    )

    return response


def extract_files(path: dict) -> list[str]:
    """Get the list of folders to further extract files and clean up the appearance of them."""

    clean_folder = []
    for item in path:
        folder = item['html_url'].split("main/")[1]
        clean_folder.append(folder.replace('%20', ' '))
    return clean_folder


def create_clean_paths(path: dict) -> list[str]:
    """If there is an .md file then it cleans up last part of the file for easier viewing. If it's a folder then it goes to extract_files() to get the clean list of folders."""

    clean_filepath = []
    for item in path:
        if ".md" in item['html_url']:
            url = item['html_url']
            file_path = url.split("main/")[1]
            clean_filepath.append(file_path.replace('%20', ' '))
        else:
            folders = extract_files(path)
            for folder in folders:
                content = get_api_response(path=folder)
                for item in content.json():
                    url = item['html_url']
                    file_path = url.split("main/")[1]
                    clean_filepath.append(file_path.replace('%20', ' '))

    return clean_filepath


def get_quote(path: dict) -> dict:
    """Review the MD file, if a quote exists then it do some clean up and add all quotes to a dict to return."""

    quote_dict = {}

    for item in path:
        content = get_api_response(path=item)
        note = markdown.markdown(content.text)

        if '[!quote]' in note:
            filter_note = ''.join(re.findall(
                r'!quote]*\s*((?:.|\n)*?)</p>', note))
            clean_note = filter_note.split('Quote by ')
            all_quotes = list(filter(None, [i.strip() for i in clean_note]))

            for item in all_quotes:
                author = item.split('[[')[1].split(']]')[0]
                quote = item.split(']]\n')[1]
                quote_dict[author] = quote

    return quote_dict


def get_md_note(path: dict) -> dict:
    """Randomly select a note url from the path, request the content of it, convert it to markdown, and clean up the note before returning it as the final product."""

    md_file = random.choice(path)
    md_file_content = get_api_response(path=md_file)

    md_formatted_note = markdown.markdown(md_file_content.text)
    if 'sharable: No' in md_formatted_note:
        get_md_note(path)
    else:
        if '<h1>Notes</h1>' in md_formatted_note:
            for line in md_formatted_note.split('\n'):
                if 'title:' in line:
                    title = re.sub(
                        r'<.*?>', '', line).replace('title:', '').strip()
            note = re.findall(r'<h1>Notes.*',
                              md_formatted_note, re.DOTALL)[0]
            return f'<h3>Note Title: {title}</h3>\n {note}'
        else:
            get_md_note(path)


def get_content(path: str, quote: bool = False) -> str:
    """Go through the process of getting a note for the email."""

    response = get_api_response(path=f'{path}')
    cleaned_paths = create_clean_paths(response.json())
    if quote == False:
        """If False then retrieve a single note from the available markdown files."""

        note = get_md_note(cleaned_paths)
        return note
    else:
        """If True then read through the available markdown files to find all the quotes then select a single quote."""

        find_quote = get_quote(cleaned_paths)
        random_quote = random.choice(list(find_quote.items()))
        quote = {"author": random_quote[0], "quote": random_quote[1]}
        return quote


quote = get_content(path='400 - Archive/300 - Literature Notes', quote=True)
note = get_content(path='200 - Citadel', quote=False)
