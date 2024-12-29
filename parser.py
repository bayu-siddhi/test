import re
import pandas as pd


class WhatssAppParser:

    def __init__(self) -> None:    
        self.pattern = {
            'datetime': r'^(\d+\/\d+\/\d+ \d+\.\d+) -',
            'username':  r'- (.*?): ',
            'message_system': r'- (.*)$',
            'message_first_line': r': (.*)$',
            'message_new_line': r'(.*)',
            'attachment_file': r'(.*) \(file terlampir\)'  # TODO: Make it accept user input
        }

    def parse(self, path: str) -> list[dict]:
        """Parse WhatsApp export chat file (.txt) to Pandas DataFrame and .csv file"""

        assert path.endswith('.txt'), "Files must be in .txt extension"
        chat_message_history = list()

        with open(path, 'r', encoding='utf8') as file:
            chat_message_index = 0
            for row in file: 
                row = row.strip()
                datetime = re.search(self.pattern['datetime'], row)  # Get message datetime
                if datetime is not None:  # Check if there is a datetime
                    username = re.search(self.pattern['username'], row)  # Get message username
                    if username is not None: 
                        # If there is a username then it is a message from the user
                        chat_message = re.search(self.pattern['message_first_line'], row)[1]
                        attachment_file = re.search(self.pattern['attachment_file'], chat_message)
                        if attachment_file is not None:
                            # If there is an attachment file, save the file name.
                            data = {
                                'datetime': datetime[1],
                                'username': username[1],
                                'message': attachment_file[1].replace(u'\u200e', ''), # Hapus U+200E
                                'is_file': True
                            }
                        else: 
                            # If there is no attachment file then it is a normal message.
                            data = {
                                'datetime': datetime[1],
                                'username': username[1],
                                'message': chat_message,
                                'is_file': False
                            }
                    else: 
                        # If there is no username then the message is a message from SYSTEM.
                        data = {
                            'datetime': datetime[1],
                            'username': "SYSTEM",
                            'message': re.search(self.pattern['message_system'], row)[1],
                            'is_file': False 
                        }
                    chat_message_history.append(data) 
                    chat_message_index += 1
                else: 
                    # If there is no datetime then the message is a continuation of the previous message.
                    message_new_line = re.search(self.pattern['message_new_line'], row)[1]
                    previous_chat_message_history = chat_message_history[chat_message_index - 1]
                    if previous_chat_message_history['is_file']:
                        # Jika sebelumnya adalah file attachment maka pesan selanjutnya harus jadi pesan terpisah
                        data = previous_chat_message_history.copy()
                        data['message'] = message_new_line
                        data['is_file'] = False
                        chat_message_history.append(data)  # Save messages to chat_message_history list
                        chat_message_index += 1  # Increment nilai index pesan
                    else: 
                        # If not an attachment file then merge the current message with the previous message
                        previous_chat_message = previous_chat_message_history['message']
                        chat_message_history[chat_message_index - 1]['message'] = f"{previous_chat_message}<br>{message_new_line}"

        df = pd.DataFrame(chat_message_history)
        df['datetime'] = pd.to_datetime(df['datetime'], format='%d/%m/%y %H.%M')
        csv_file = path[:-3] + 'csv'
        df.to_csv(csv_file, index=False)

        return chat_message_history
