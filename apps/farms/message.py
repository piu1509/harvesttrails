"""Class for farm messages"""

class FarmMessage:
    INVALID_CSV_FORMAT = f"CSV file format is invalid. \
                \nPlease check the format and try again"
    MISSING_ROWS = f"Rows are missing in your CSV file, \
                please upload the file with data."

    def farm_created(num : int):
        """Function to return message
        when n number of farm(s) are created

        Args:
            num (int): number of forms

        Returns:
            str : string
        """
        return f"{num} Farm(s) created successfully."