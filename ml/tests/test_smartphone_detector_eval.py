import pytest
from src.evaluate_smartphone_detector import parse_polygon_annotation


def test_parse_polygon_annotation_extracts_only_wbc_boxes(tmp_path):
    path = tmp_path / "annotation.txt"
    path.write_text(
        "2,100,80\n"
        "1-1,Uninfected,No_comment,Polygon,4,2,3,10,3,10,12,2,12\n"
        "1-2,White_Blood_Cell,No_comment,Polygon,4,20,30,40,30,40,50,20,50\n",
        encoding="utf-8",
    )

    width, height, boxes = parse_polygon_annotation(path)

    assert (width, height) == (100, 80)
    assert boxes == [(20.0, 30.0, 40.0, 50.0)]


def test_parse_polygon_annotation_rejects_out_of_bounds_wbc(tmp_path):
    path = tmp_path / "annotation.txt"
    path.write_text(
        "1,100,80\n"
        "1-1,White_Blood_Cell,No_comment,Polygon,3,20,30,110,30,40,50\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="outside image bounds"):
        parse_polygon_annotation(path)


def test_parse_polygon_annotation_checks_object_count(tmp_path):
    path = tmp_path / "annotation.txt"
    path.write_text("2,100,80\n1-1,Uninfected,No_comment,Polygon,3,2,3,10,3,10,12\n")

    with pytest.raises(ValueError, match="object count differs"):
        parse_polygon_annotation(path)
