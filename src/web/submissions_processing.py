from icecream import ic


def merge_fields_with_submission_data(
    fields: list, data: dict, excluded_labels=[]
) -> list:
    results = []
    for field in fields:
        if field.get("inputs"):
            input_fields = []
            for input_field in field.get("inputs"):
                input_id = str(input_field.get("id"))
                label = input_field.get("label")
                value = data.get(input_id, "")
                _type = input_field.get("type")
                if not _type:
                    _type = field.get("type")

                if value:
                    input_fields.append({"label": label, "value": value, "type": _type})

            label = field.get("label")
            _type = field.get("type")

            if label not in excluded_labels:
                results.append({"label": label, "type": _type, "inputs": input_fields})

        elif field.get("type") == "list":
            results.append({"label": field.get("label"), "type": "text"})
            for list_data in data.get(str(field.get("id"))):
                input_fields = []

                for input_field in field.get("choices"):
                    input_id = str(input_field.get("text"))
                    label = input_field.get("text")
                    value = list_data.get(input_id, "")

                    _type = input_field.get("type")
                    if not _type:
                        _type = field.get("type")

                    if value:
                        input_fields.append(
                            {"label": label, "value": value, "type": _type}
                        )

                    label = field.get("label")
                    _type = field.get("type")

                if label not in excluded_labels:
                    results.append({"label": "", "type": _type, "inputs": input_fields})
        else:
            label = field.get("label")
            field_id = str(field.get("id"))
            value = data.get(field_id, "")
            _type = field.get("type")

            if label not in excluded_labels:
                if _type == "section" or value:
                    results.append({"label": label, "value": value, "type": _type})

    return results
