"""Class for field messages"""

class FieldMessage:
    INVALID_CSV_FORMAT = f"CSV file format is invalid. \
                \nPlease check the format and try again"
    MISSING_ROWS = f"Rows are missing in your CSV file, \
                please upload the file with data."
    INVALID_DATE_FORMAT = "Date-time related data is not in a proper \
                format in the CSV file. Valid format is \"YYYY-MM-DD HH:MM\".\
                     Please check the file and try again."

    def field_created(num : int):
        """Function to return message
        when n number of field(s) are created

        Args:
            num (int): number of field

        Returns:
            str : string
        """
        return f"{num} Field(s) created successfully."