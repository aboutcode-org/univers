from univers.versions import RPMVersion

# all similar length, no pkgrel
def test_same_length():
    assert RPMVersion("1.5.0") == RPMVersion("1.5.0")
    assert RPMVersion("1.5.1") > RPMVersion("1.5.0")


# mixed length
def test_mixed_length():
    assert RPMVersion("1.5.1") > RPMVersion("1.5")


# with pkgrel, simple
def test_with_pkgrel_same_length():
    assert RPMVersion("1.5.0-1") == RPMVersion("1.5.0-1")
    assert RPMVersion("1.5.0-1") < RPMVersion("1.5.0-2")
    assert RPMVersion("1.5.0-1") < RPMVersion("1.5.1-1")
    assert RPMVersion("1.5.0-2") < RPMVersion("1.5.1-1")


# going crazy? alpha-dotted versions
def test_alpha_dotted():
    assert RPMVersion("1.5.a") > RPMVersion("1.5  ")
    assert RPMVersion("1.5.b") > RPMVersion("1.5.a")
    assert RPMVersion("1.5.1") > RPMVersion("1.5.b")


# epoch included version comparisons
def test_with_epoch():
    assert RPMVersion("0:1.0") == RPMVersion("0:1.0")
    assert RPMVersion("0:1.0") < RPMVersion("0:1.1")
    assert RPMVersion("1:1.0") > RPMVersion("0:1.0")
    assert RPMVersion("1:1.0") > RPMVersion("0:1.1")
    assert RPMVersion("1:1.0") < RPMVersion("2:1.1")


# epoch + sometimes present pkgrel
def test_with_epoch_mixed_pkgrel():
    assert RPMVersion("1:1.0") > RPMVersion("0:1.0-1")
    assert RPMVersion("1:1.0-1") > RPMVersion("0:1.1-1")


# # epoch included on one version
# def test_with_only_one_version_with_epoch():
#     assert RPMVersion("0:1.0")  ==  RPMVersion("1.0")
#     assert RPMVersion("0:1.0")  <  RPMVersion("1.1")
#     assert RPMVersion("0:1.1")  >  RPMVersion("1.0")
#     assert RPMVersion("1:1.0")  >  RPMVersion("1.0")
#     assert RPMVersion("1:1.0")  >  RPMVersion("1.1")
#     assert RPMVersion("1:1.1")  >  RPMVersion("1.1")

# # alpha dots and dashes
# def test_alpha_dot_dash():
#     assert RPMVersion("1.5.b-1") == RPMVersion("1.5.b")
#     assert RPMVersion("1.5-1") < RPMVersion("1.5.b")

# # same/similar content, differing separators
# def test_same_content_different_separators():
#     assert RPMVersion("2.0") == RPMVersion("2_0")
#     assert RPMVersion("2.0_a") == RPMVersion("2_0.a")
#     assert RPMVersion("2.0a ") < RPMVersion("2.0.a")
#     assert RPMVersion("2___a") == RPMVersion("2_a")

# # with pkgrel, mixed lengths
# def test_with_pkgrel_mixed_length():
#     assert RPMVersion("1.5-1") < RPMVersion("1.5.1-1")
#     assert RPMVersion("1.5-2") < RPMVersion("1.5.1-1")
#     assert RPMVersion("1.5-2") < RPMVersion("1.5.1-2")

# # mixed pkgrel inclusion
# def test_with_pkgrel_mixed():
#     assert RPMVersion("1.5") ==  RPMVersion("1.5-1")
#     assert RPMVersion("1.5-1") ==  RPMVersion("1.5  ")
#     assert RPMVersion("1.1-1") ==  RPMVersion("1.1  ")
#     assert RPMVersion("1.0-1") <  RPMVersion("1.1  ")
#     assert RPMVersion("1.1-1") > RPMVersion("1.0  ")

# # alphanumeric versions
# assert RPMVersion("1.5b-1") < RPMVersion("1.5-1")
# assert RPMVersion("1.5b  ") < RPMVersion("1.5  ")
# assert RPMVersion("1.5b-1") < RPMVersion("1.5  ")
# assert RPMVersion("1.5b  ") < RPMVersion("1.5.1")

# # from the manpage
# def test_manpage_cases():
#     assert RPMVersion("1.0a") < RPMVersion("1.0alpha")
#     assert RPMVersion("1.0alpha") < RPMVersion("1.0b")
#     assert RPMVersion("1.0b") < RPMVersion("1.0beta")
#     assert RPMVersion("1.0beta") < RPMVersion("1.0rc")
#     assert RPMVersion("1.0rc") < RPMVersion("1.0")
