from os.path import sep
from os import remove


def additional_packaging(ta_name=None):
    pass


def cleanup_output_files(output_path: str, ta_name: str) -> None:
    """
    prepare a list for the files to be deleted after the source code has been copied to output directory
    :param output_path: The path provided in `--output` argument in ucc-gen command or the default output path.
    :param ta_name: The add-on name which is passed as a part of `--addon-name` argument during `ucc-gen init`
                    or present in app.manifest file of add-on.
    """
    files_to_delete = []
    files_to_delete.append(sep.join([output_path, ta_name, "lib", ".gitkeep"]))

    for delete_file in files_to_delete:
        try:
            remove(delete_file)
        except FileNotFoundError:
            # simply pass if the file doesn't exist
            pass
