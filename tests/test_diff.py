from codemodder.diff import calc_line_num_changes


def test_calc_line_nums_remove_line():
    lines = [
        "--- \n",
        "+++ \n",
        "@@ -5,7 +5,6 @@\n",
        "     port: 443,\n",
        "     path: '/',\n",
        "     method: 'GET',\n",
        "-    checkServerIdentity: function() {},\n",
        " };\n",
        " \n",
        " const req = https.request(options, (res) => {\n",
    ]
    assert calc_line_num_changes(lines) == [8]


def test_calc_line_nums_add_line():
    lines = [
        "--- original.py",
        "+++ modified.py",
        "@@ -1,3 +1,4 @@",
        " def test_name(self):",
        "     codemod = get_codemod()",
        "+    print(codemod)",
        '     assert codemod.name == "django", f"incorrect name"',
    ]
    assert calc_line_num_changes(lines) == [3]


def test_calc_line_nums_change_same_line():
    lines = [
        "--- original.py",
        "+++ modified.py",
        "@@ -1,4 +1,4 @@",
        " def test_name(self):",
        "     codemod = get_codemod()",
        "-    assert codemod.name == 'django'",
        "+    assert codemod.name == 'django', f'incorrect name'",
    ]
    assert calc_line_num_changes(lines) == [3]


def test_calc_line_nums_multiple_hunks():
    lines = [
        "--- one.txt	2024-06-28 11:52:23",
        "+++ two.txt	2024-06-28 11:52:13",
        "@@ -1,3 +1,9 @@",
        " def test_name(self):",
        "     codemod = get_codemod()",
        "+    print(codemod)",
        '     assert codemod.name == "django", f"incorrect name"',
        '+    print("test OK")',
        "+",
        "+",
        "+def test_new():",
        "+    pass",
    ]
    assert calc_line_num_changes(lines) == [3, 5, 6, 7, 8, 9]
