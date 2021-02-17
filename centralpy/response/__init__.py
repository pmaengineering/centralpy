from centralpy.response.csvzip import CsvZip


class Response:
    def __init__(self, response):
        self.response = response

    def json(self):
        return self.response.json()
