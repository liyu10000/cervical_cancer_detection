import os


def get_path_postfix(filename):
    return os.path.splitext(filename)[1]


class FileScanner(object):
    """
    获取文件列表工具类
    """

    def __init__(self, files_path, postfix=None):
        """

        :param files_path: 待扫描文件路径
        :param postfix: 所需文件后缀，['.tif', '.kfb'], 默认为空，即获取该路径下所有文件
        """
        self.files_path = files_path

        if postfix:
            assert isinstance(postfix, list), 'argument [postfix] should be list'

        files = []
        if os.path.isfile(files_path):
            if postfix:
                ctype = get_path_postfix(files_path)
                if ctype in postfix:
                    files.append(files_path)
            else:
                files.append(files_path)

        if os.path.isdir(files_path):
            for root, dirs, filenames in os.walk(files_path):
                for filename in filenames:
                    if postfix:
                        ctype = get_path_postfix(filename)
                        if ctype in postfix:
                            files.append(os.path.join(root, filename))
                    else:
                        files.append(os.path.join(root, filename))
        # 替换为绝对路径
        files = [os.path.abspath(item) for item in files]

        self.files = files

    def get_files(self):
        return self.files


def generate_name_path_dict(path, postfix=None):
    """
    获取大图文件路径 key: value = 文件名：文件路径
    :param path: 待检索文件路径列表
    :param postfix: 回收文件类型 ['.tif', '.kfb']
    :return: {filename: file_abs_path}
    """

    assert isinstance(path, (str, list)), 'argument [path] should be path or path list'

    files_collection = []

    if isinstance(path, list):
        for item in path:
            files_collection.extend(FileScanner(item, postfix).get_files())
    else:
        files_collection = FileScanner(path, postfix).get_files()

    dict_ = {}
    for file in files_collection:
        key, _ = os.path.splitext(os.path.basename(file))
        dict_[key] = file

    return dict_
