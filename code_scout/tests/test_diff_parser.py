from io import StringIO

from unidiff import PatchSet

from core.utils.diff_parser import parse_diff_string

# Test diff content from diff.txt (real-world example)
TEST_DIFF_CONTENT = """
diff --git a/flutter/pubspec.yaml b/flutter/pubspec.yaml
index b39ff9c..c9c453e 100644
--- a/flutter/pubspec.yaml
+++ b/flutter/pubspec.yaml
@@ -4,47 +4,47 @@ publish_to: 'none' # Remove this line if you wish to publish to pub.dev
 version: 1.0.0+1

 environment:
-  sdk: '>=3.1.3 <4.0.0'
+  sdk: '>=3.4.0 <4.0.0'
 dependencies:
   flutter:
     sdk: flutter
-  cupertino_icons: 1.0.6
+  cupertino_icons: ^1.0.8

   flutter_localizations:
     sdk: flutter

   # architecture
-  bloc: 8.1.2
-  flutter_bloc: 8.1.3
+  bloc: ^9.0.0
+  flutter_bloc: ^9.0.0

   # dependency injection
-  get_it: 7.6.4
+  get_it: ^8.0.3

   # functional programming, used for Either type
   dartz: 0.10.1

   # equality checks
-  equatable: 2.0.5
+  equatable: ^2.0.7

   # localization
-  intl: 0.18.1
+  intl: ^0.19.0

   # widgets
-  gap: 3.0.1
-  flex_color_scheme: 7.3.1
-  google_fonts: 6.1.0
-  grouped_list: 5.1.2
+  gap: ^3.0.1
+  flex_color_scheme: ^8.1.0
+  google_fonts: ^6.2.1
+  grouped_list: ^6.0.0

   #navigation
-  go_router: 13.0.1
+  go_router: ^14.6.3

   # utils
-  collection: 1.18.0
-  flutter_dotenv: 5.1.0
+  collection: ^1.19.0
+  flutter_dotenv: ^5.2.1

   # Analytics
-  wiredash: 1.9.0
-  sentry_flutter: 7.14.0
+  wiredash: 2.3.0
+  sentry_flutter: ^8.12.0



@@ -56,7 +56,7 @@ dev_dependencies:
     sdk: flutter

   # code analysis
-  flutter_lints: ^3.0.1
+  flutter_lints: ^5.0.0

   # tests
   golden_toolkit: 0.15.0
@@ -64,21 +64,21 @@ dev_dependencies:
     git:
       url: https://github.com/Betterment/alchemist
       ref: main
-  mocktail_image_network: 1.0.0
-  mocktail: 1.0.2
-  bloc_test: 9.1.5
+  mocktail_image_network: ^1.2.0
+  mocktail: ^1.0.4
+  bloc_test: ^10.0.0
   import_sorter: 4.6.0

   hive_generator: 2.0.1
   # needed by hive_generator
-  build_runner: 2.4.7
+  build_runner: ^2.4.14

   # utils
-  meta: 1.10.0
+  meta: ^1.15.0
   recase: 4.1.0
-  uuid: 4.3.2
+  uuid: ^4.5.1

-  flutter_launcher_icons: 0.13.1
+  flutter_launcher_icons: ^0.14.2

 flutter:
   uses-material-design: true

"""


def test_parse_diff_string_empty_diff():
    """
    Test parsing an empty diff string.
    """
    parsed_diff = parse_diff_string("", filename="test.txt")
    assert parsed_diff is None


def test_parse_diff_string_github_diff():
    """
    Test parsing a real-world GitHub diff with multiple files and hunks.
    """
    # The unidiff library's PatchSet can parse multiple files from a single diff string.
    # We need to iterate over the PatchSet to get individual PatchedFile objects.
    patch_set = PatchSet(StringIO(TEST_DIFF_CONTENT))
    parsed_files = [parse_diff_string(str(pf), filename="test.txt") for pf in patch_set]

    assert len(parsed_files) == 2

    # Test for the first file: code_index_extractor.py
    file1 = parsed_files[0]
    assert file1 is not None
    assert file1.source_file == "code_scout/src/core/code_index/code_index_extractor.py"
    assert file1.target_file == "code_scout/src/core/code_index/code_index_extractor.py"
    assert file1.is_modified_file is True
    assert file1.is_added_file is False
    assert file1.is_removed_file is False
    assert file1.is_renamed_file is False
    assert len(file1.hunks) == 3
