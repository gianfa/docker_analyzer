"""Data Views utilities
"""


def convert_dataframe_to_json(df):
    """Convert DataFrame to a serializable format."""
    return {"columns": df.columns.tolist(), "data": df.values.tolist()}


def convert_df_views_to_json(views):
    return [
        {
            "title": view["title"],
            "description": view["description"],
            "df": convert_dataframe_to_json(view["df"]),
        }
        for view in views
    ]
