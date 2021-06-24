from icecream import ic


def merge_fields_with_submission_data(fields: list, data: dict) -> list:
    results = []
    for field in fields:
        if field.get("inputs"):
            for input_field in field.get("inputs"):
                input_id = str(input_field.get("id"))
                label = input_field.get("label")
                value = data.get(input_id, "")
                _type = input_field.get("type")
                if not _type:
                    _type = field.get("type")
                results.append({"label": label, "value": value, "type": _type})
        else:
            label = field.get("label")
            field_id = str(field.get("id"))
            value = data.get(field_id, "")
            _type = field.get("type")

            results.append({"label": label, "value": value, "type": _type})

    return results
