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
            'attachment_file': r'(.*) \(file terlampir\)'  # Buat agar diterima dari input user
        }

    def parse(self, path: str) -> list[dict]:
        """Parse WhatsApp export chat file (.txt) to Pandas DataFrame and .csv file"""

        assert path.endswith('.txt'), "Files must be in .txt extension"
        chat_message_history = list()

        with open(path, 'r', encoding='utf8') as file:
            chat_message_index = 0
            for row in file: 
                row = row.strip()
                datetime = re.search(self.pattern['datetime'], row)  # Mendapatkan datetime pesan
                if datetime is not None:  # Cek apakah ada datetime
                    username = re.search(self.pattern['username'], row)  # Mendapatkan username pesan
                    if username is not None: 
                        # Jika ada username maka itu merupakan pesan dari pengguna
                        chat_message = re.search(self.pattern['message_first_line'], row)[1]
                        attachment_file = re.search(self.pattern['attachment_file'], chat_message)
                        if attachment_file is not None:
                            # Jika ada file attachment maka simpan nama file nya
                            data = {
                                'datetime': datetime[1],
                                'username': username[1],
                                'message': attachment_file[1],
                                'is_file': True
                            }
                        else: 
                            # Jika tidak ada file attachment maka merupakan pesan biasa
                            data = {
                                'datetime': datetime[1],
                                'username': username[1],
                                'message': chat_message,
                                'is_file': False
                            }
                    else: 
                        # Jika tidak ada username maka pesan itu merupakan pesan dari SYSTEM
                        data = {
                            'datetime': datetime[1],
                            'username': "SYSTEM",
                            'message': re.search(self.pattern['message_system'], row)[1],
                            'is_file': False 
                        }
                    chat_message_history.append(data) 
                    chat_message_index += 1
                else: 
                    # Jika tidak ada datetime maka pesan itu merupakan lanjutan dari pesan sebelumnya
                    message_new_line = re.search(self.pattern['message_new_line'], row)[1]
                    previous_chat_message_history = chat_message_history[chat_message_index - 1]
                    if previous_chat_message_history['is_file']:
                        # Jika sebelumnya adalah file attachment maka pesan selanjutnya harus jadi pesan terpisah
                        data = previous_chat_message_history.copy()
                        data['message'] = message_new_line
                        data['is_file'] = False
                        chat_message_history.append(data)  # Simpan pesan ke list chat_message_history
                        chat_message_index += 1  # Increment nilai index pesan
                    else: 
                        # Jika bukan file attachment maka gabungkan pesan saat ini dengan pesan sebelumnya
                        previous_chat_message = previous_chat_message_history['message']
                        chat_message_history[chat_message_index - 1]['message'] = f"{previous_chat_message}<br>{message_new_line}"

        df = pd.DataFrame(chat_message_history)
        df['datetime'] = pd.to_datetime(df['datetime'], format='%d/%m/%y %H.%M')
        csv_file = path[:-3] + 'csv'
        df.to_csv(csv_file, index=False)

        return chat_message_history


if __name__=="__main__":
    import os
    chat_directory = 'chat'
    chat_file = 'Chat WhatsApp dengan Qudsiyah Zahra.txt'
    path = os.path.join(chat_directory, chat_file)
    wa_parser = WhatssAppParser()
    wa_parser.parse(path)
