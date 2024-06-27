from collections import deque

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
    assert calc_line_num_changes(lines) == deque([8])
