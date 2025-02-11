def common_choice_response(value_key='id', display_key='name', queryset=[], default=None):
    options = []

    for option in queryset:
        options.append({
            "value": getattr(option, value_key),
            "display_name": getattr(option, display_key)
        })

    return {
        "default": default,
        "options": options
    }


def get_file_details(file_name):
    file_name = file_name.split('AgrStringFile')

    file_details = {}

    file_details['latitude'] = file_name[0]
    file_details['longitude'] = file_name[1]
    file_details['ImageDateTime'] = file_name[2]
    file_details['fileName'] = file_name[3]

    return file_details


