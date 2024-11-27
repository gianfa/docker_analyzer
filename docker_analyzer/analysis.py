import itertools

import numpy as np
import pandas as pd

from docker_analyzer.config import (
    LAYERS_SIMILARITY_FUNCTION,
    LAYOUT_SIMILARITY_THRESHOLD,
)
from docker_analyzer.inspection_io import get_image_history
from docker_analyzer.logger import get_logger

logger = get_logger(__name__)


def compute_series_elements_similarity(
    s_a: pd.Series,
    s_b: pd.Series,
    matching_function: callable = lambda x, y: LAYERS_SIMILARITY_FUNCTION(x, y),
    threshold: int = LAYOUT_SIMILARITY_THRESHOLD,
) -> pd.DataFrame:
    """Compute series similarity

    Parameters
    ----------
    s_a : pd.Series
        First series to compare.
    s_b : pd.Series
        Second series to compare.
    matching_function : callable, optional
        The function to use to match each element from `s_a` against each element from `s_b`.
    threshold : int, optional
        A threshold to cut the result. Results above it will be retained, by default 50.

    Returns
    -------
    pd.DataFrame
        ...

    Example
    -------
    >>> matching_function = lambda x,y: fuzz.ratio(x, y)
    >>> s_a = ns.loc[~ns['Size_MB_img1'].isnull(), 'CreatedBy']
    >>> s_b = ns.loc[~ns['Size_MB_img2'].isnull(), 'CreatedBy']
    >>> threshold = 50
    >>> compute_series_elements_similarity(s_a, s_b)
    """
    cprod = pd.DataFrame(list(itertools.product(s_a, s_b)))
    cprod["result"] = cprod.apply(
        lambda row: matching_function(row.iloc[0], row.iloc[1]), axis=1
    )
    cprod = cprod.sort_values("result", ascending=False)
    if threshold is None:
        return cprod
    return cprod[cprod["result"] > threshold]


# -- get --


def get_duplicated_layers(img_name: str) -> pd.DataFrame:
    df = get_image_history(img_name)
    return df[df.duplicated(subset=["CreatedBy"])].sort_values("CreatedBy")


def get_non_shared_layers(img_name_1: str, img_name_2: str, img_n=None) -> pd.DataFrame:
    """Get non shared layers between two images"""
    df1 = get_image_history(img_name_1)
    df2 = get_image_history(img_name_2)

    merged = pd.merge(
        df1,
        df2,
        on="CreatedBy",
        how="outer",
        suffixes=("_img1", "_img2"),
        indicator=True,
    )

    non_shared_df = merged[merged["_merge"] != "both"].copy()
    non_shared_df["Source"] = (
        non_shared_df["_merge"]
        .map({"left_only": "img1", "right_only": "img2"})
        .drop(columns=["_merge"])
    )
    if img_n not in [1, 2]:
        return non_shared_df
    excluded_img = 1 if img_n == 2 else 2
    excluded_img_cols = non_shared_df.columns[
        non_shared_df.columns.str.endswith(f"_img{excluded_img}")
    ]
    return non_shared_df[non_shared_df["Source"] == f"img{img_n}"].drop(
        columns=excluded_img_cols
    )


def get_shared_layers(
    img_name_1: str, img_name_2: str, drop_duplicates: bool = False
) -> pd.DataFrame:
    "Get shared layers between two images"
    df1 = get_image_history(img_name_1)
    df2 = get_image_history(img_name_2)

    if not drop_duplicates:
        return pd.merge(
            df1,
            df2,
            on="CreatedBy",
            how="inner",
            suffixes=("_img1", "_img2"),
            indicator=True,
        ).drop(columns=["_merge"])
    return pd.merge(
        df1.drop_duplicates(subset="CreatedBy"),
        df2.drop_duplicates(subset="CreatedBy"),
        on="CreatedBy",
        how="inner",
        suffixes=("_img1", "_img2"),
        indicator=True,
    ).drop(columns=["_merge"])


def get_img_added_size(imga_name_1, imga_name_2, img_n=1) -> pd.DataFrame:
    """Get added size of an image (imga_name_2), with respect to another image
    (imga_name_1), based on the non shared layers.
    """
    return (
        get_non_shared_layers(imga_name_1, imga_name_2)
        .groupby("Source")[f"Size_MB_img{img_n}"]
        .sum()
    ).loc[f"img{img_n}"]


# -- compare --


# TODO: turn into *make_analysis*
def compare_histories(img_name_1, img_name_2, show=False) -> dict:
    """
    Compares the histories of two Docker images and prints differences in layers.

    Parameters:
        img_name_1 (str): first image name.
        img_name_2 (str): second image name.
    """
    # Load histories from JSON files
    df1 = get_image_history(img_name_1)
    df2 = get_image_history(img_name_2)

    # Display layers with missing IDs or different sizes
    if show:
        logger.info("\nComparing image layers:")

    merged = pd.merge(
        df1,
        df2,
        on="CreatedBy",
        how="outer",
        suffixes=("_img1", "_img2"),
        indicator=True,
    )

    # Layers only in the first image
    only_in_img1 = get_non_shared_layers(img_name_1, img_name_2, img_n=1)
    if not only_in_img1.empty:
        print("\nLayers only in the first image:")
        print(len(only_in_img1))

    # Layers only in the second image
    only_in_img2 = get_non_shared_layers(img_name_1, img_name_2, img_n=2)
    if show and only_in_img2.empty:
        logger.info("\nLayers only in the second image:")
        logger.info(len(only_in_img2))

    # Layers in both images but with different sizes
    tol = 0.1
    both_images = get_shared_layers(img_name_1, img_name_2)
    size_diff = both_images[
        (both_images["Size_MB_img1"] - both_images["Size_MB_img2"]) > tol
    ]
    if show and not size_diff.empty:
        logger.info("\nLayers with different sizes:")
        logger.info(
            size_diff[
                ["Id_img1", "Size_MB_img1", "Size_MB_img2", "Id_img2", "CreatedBy"]
            ]
        )

    return {
        "only_in_img1": only_in_img1,
        "only_in_img2": only_in_img2,
        "diff_in_size": both_images,
        "size_diff": size_diff,
    }


def compare_total_sizes(img_name_1, img_name_2) -> pd.DataFrame:
    """Compare two images total size"""
    df1 = get_image_history(img_name_1)
    df2 = get_image_history(img_name_2)

    return pd.DataFrame(
        {
            "img1": [df1["Size_MB"].sum()],
            "img2": [df2["Size_MB"].sum()],
            "difference": [df1["Size_MB"].sum() - df2["Size_MB"].sum()],
        },
        index=["Size_MB"],
    )


def compare_number_of_layers(img_name_1, img_name_2) -> pd.DataFrame:
    """Compare two images number of layers"""
    df1 = get_image_history(img_name_1)
    df2 = get_image_history(img_name_2)

    return pd.DataFrame(
        {
            "img1": [df1.shape[0]],
            "img2": [df2.shape[0]],
            "difference": [df1.shape[0] - df2.shape[0]],
        },
        index=["layers_count"],
    )


def compare_duplicated(img_name_1, img_name_2) -> pd.DataFrame:
    """Compare two images duplicated layers"""
    df1 = get_duplicated_layers(img_name_1)
    df2 = get_duplicated_layers(img_name_2)
    return pd.DataFrame(
        data={
            "img1": [df1.shape[0], df1["Size_MB"].sum()],
            "img2": [df2.shape[0], df2["Size_MB"].sum()],
            "difference": [
                df1.shape[0] - df2.shape[0],
                df1["Size_MB"].sum() - df2["Size_MB"].sum(),
            ],
        },
        index=["duplicated", "duplicated_total_size"],
    )


def compare_shared_layers(
    imga_name_1: str, imga_name_2: str, on: str, drop_duplicates: bool = False
) -> pd.DataFrame:
    """Compare two images shared layers"""
    shared = get_shared_layers(imga_name_1, imga_name_2, drop_duplicates)
    shared = shared[["CreatedBy", f"{on}_img1", f"{on}_img2"]]
    shared["difference"] = shared[f"{on}_img1"] - shared[f"{on}_img2"]
    return shared.sort_values("difference", ascending=False)


def compare_non_shared_layers(
    img_name_1: str, img_name_2: str, on: str
) -> pd.DataFrame:
    ns = get_non_shared_layers(img_name_1, img_name_2)
    ns = ns[
        (ns["Size_MB_img1"] > LAYOUT_SIMILARITY_THRESHOLD)
        | (ns["Size_MB_img2"] > LAYOUT_SIMILARITY_THRESHOLD)
    ]
    ns = ns.sort_values(["Size_MB_img1", "Size_MB_img2"], ascending=False)
    ns = ns[["CreatedBy", f"{on}_img1", f"{on}_img2"]]
    ns["difference"] = ns[f"{on}_img1"] - ns[f"{on}_img2"]
    return ns


# TODO: signature doesn't use img_name
def compare_layers_command(
    createdby_1, createdby_2, matching_function, show=True
) -> str:

    diffs = matching_function(createdby_1, createdby_2)

    # ANSI codes
    red = "\033[91m"
    green = "\033[92m"
    reset = "\033[0m"

    comparison = []
    for diff in diffs:
        if diff.startswith("+"):
            comparison.append(f"{green}{diff}{reset}")
        elif diff.startswith("-"):
            comparison.append(f"{red}{diff}{reset}")
        else:
            comparison.append(diff)

    comparison = "\n".join(comparison)

    if show:
        print(comparison)
    return diffs


# TODO: signature doesn't use img_name
def compute_layers_similarity(
    df: pd.DataFrame,
    matching_function: callable = LAYERS_SIMILARITY_FUNCTION,
    threshold: int = LAYOUT_SIMILARITY_THRESHOLD,
) -> pd.DataFrame:
    return compute_series_elements_similarity(
        s_a=df.loc[~df["Size_MB_img1"].isnull(), "CreatedBy"],
        s_b=df.loc[~df["Size_MB_img2"].isnull(), "CreatedBy"],
        matching_function=matching_function,
        threshold=threshold,
    ).rename(columns={0: "img1", 1: "img2"})


def get_layers_similarities_from_2_images(
    img_name_1,
    img_name_2,
    size_th_min=10,  # minimum size to consider layers
    matching_function: callable = LAYERS_SIMILARITY_FUNCTION,
):
    """"""

    df1 = get_image_history(img_name_1)
    df2 = get_image_history(img_name_2)

    df1["source"] = "img1"
    df2["source"] = "img2"
    merged = pd.concat([df1, df2], ignore_index=True)
    merged = merged[merged["Size_MB"] > size_th_min]

    cprod = pd.DataFrame(
        data=list(itertools.product(merged["CreatedBy"], merged["CreatedBy"])),
        columns=["img1", "img2"],
    )
    cprod["similarity"] = cprod.apply(
        lambda row: matching_function(row["img1"], row["img2"]), axis=1
    )
    return cprod.sort_values("similarity", ascending=False)


# -- show --


def show_duplicated_layers(img_name: str, v: bool = True):
    df = get_duplicated_layers(img_name)
    if v and not df.empty:
        print(
            f"INFO| {len(df)} duplicated layers found, "
            f"for a total size of {df['Size_MB'].sum():.3f} MB"
        )
    return df


def show_layers_ne_sizes(img_name_1, img_name_2, tol_MB=1):
    df1 = get_image_history(img_name_1)
    df2 = get_image_history(img_name_2)
    merged = pd.merge(
        df1,
        df2,
        on="CreatedBy",
        how="inner",
        suffixes=("_img1", "_img2"),
        indicator=True,
    )
    sizes = merged[["CreatedBy", "Size_MB_img1", "Size_MB_img2"]]
    sizes["difference"] = sizes["Size_MB_img1"] - sizes["Size_MB_img2"]
    return sizes[(sizes["Size_MB_img1"] - sizes["Size_MB_img2"] > tol_MB)]


def make_analysis_1(image_name_1: str, image_name_2: str) -> dict:

    # -
    cs = compare_shared_layers(image_name_1, image_name_2, "Size_MB")
    logger.info(cs.sum().to_frame().T)

    # - compare history -
    cph = compare_histories(image_name_1, image_name_2)

    only_in_1 = cph["only_in_img1"]
    only_in_2 = cph["only_in_img2"]
    diff_size = cph["diff_in_size"]
    diff_size2 = cph["size_diff"]

    ns = compare_non_shared_layers(image_name_1, image_name_2, "Size_MB")

    # similarities = compute_layers_similarity(ns)

    def describe_n_exclusive_layers(df):
        if df.empty:
            return "There are no layers exclusive to img1 that are missing in img2"
        else:
            return f"There are {df.shape[0]} layers exclusive to img1"

    comparisons = [
        {
            "title": "Only in img1",
            "description": describe_n_exclusive_layers(only_in_1),
            "df": only_in_1,
        },
        {
            "title": "Only in img2",
            "description": describe_n_exclusive_layers(only_in_2),
            "df": only_in_2,
        },
        {
            "title": "Size diff",
            "description": "Layer size differences",
            "df": diff_size,
        },
        {
            "title": "Not equal layer sizes",
            "description": "Layer size differences",
            "df": ns,
        },
    ]
    return comparisons
