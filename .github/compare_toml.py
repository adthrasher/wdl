#!/usr/bin/env python3

import sys
import argparse

def compare_toml(file1, file2):
    f1_repos = {}
    f1_diagnostics = {}
    with open(file1) as f1:
        # Parse repository entries
        while line := f1.readline().strip():
            # print(line)
            if line.startswith("[repositories"):
                id = f1.readline().strip()
                commit = f1.readline().strip()
                blank = f1.readline().strip()
                if blank.startswith("filters"):
                    filters = blank
                    blank = f1.readline().strip()
                f1_repos[id] = commit
            else:
                # print("line:", line)
                # Parse diagnostic entries
                if line.startswith("[[diagnostics]]"):
                    document = f1.readline().strip().split('"')[1]
                    message = f1.readline().strip()
                    if '"' in message:
                        message = message.split('"')[1]
                    elif "'" in message:
                        message = message.split("'")[1]
                    permalink = f1.readline().strip().split('"')[1]
                    blank = f1.readline().strip()
                    if document not in f1_diagnostics:
                        f1_diagnostics[document] = []
                    # print(message)
                    file, line, character, error = message.split(":", 3)
                    diagnostic = {
                        "file": file,
                        "line": line,
                        "character": character,
                        "error": error,
                        "permalink": permalink,
                        "message": message
                    }
                    f1_diagnostics[document].append(diagnostic)
                else:
                    break
            
        # print(f1_diagnostics)

    f2_repos = {}
    f2_diagnostics = {}
    with open(file2) as f2:
        # Parse repository entries
        while line := f2.readline().strip():
            if line.startswith("[repositories"):
                id = f2.readline().strip()
                commit = f2.readline().strip()
                blank = f2.readline().strip()
                if blank.startswith("filters"):
                    filters = blank
                    blank = f2.readline().strip()
                f2_repos[id] = commit
            else:
                if line.startswith("[[diagnostics]]"):
                    document = f2.readline().strip().split('"')[1]
                    message = f2.readline().strip()
                    if '"' in message:
                        message = message.split('"')[1]
                    elif "'" in message:
                        message = message.split("'")[1]
                    permalink = f2.readline().strip().split('"')[1]
                    blank = f2.readline().strip()
                    if document not in f2_diagnostics:
                        f2_diagnostics[document] = []
                    # print(message)
                    file, line, character, error = message.split(":", 3)
                    diagnostic = {
                        "file": file,
                        "line": line,
                        "character": character,
                        "error": error,
                        "permalink": permalink,
                        "message": message
                    }
                    f2_diagnostics[document].append(diagnostic)
                else:
                    break
    
    print("File {} contains {} repositories".format(file1, len(f1_repos)))
    print("File {} contains {} repositories".format(file2, len(f2_repos)))
    shared = {k: f1_repos[k] for k in f1_repos if k in f2_repos}
    print("There are {} repositories shared between the two files".format(len(shared)))
    changed_hash = {k: f1_repos[k] for k in f1_repos if k in f2_repos and f1_repos[k] != f2_repos[k]}
    if len(changed_hash) != 0:    
        print("There are {} repositories with different commit hashes".format(len(changed_hash)))
        for repo in changed_hash:
            print("Repository {} has different commit hashes:".format(repo))
            print("    File {}: {}".format(file1, f1_repos[repo]))
            print("    File {}: {}".format(file2, f2_repos[repo]))
      
    shared_documents = {k: f1_diagnostics[k] for k in f1_diagnostics if k in f2_diagnostics}
    f1_only_documents = {k: f1_diagnostics[k] for k in f1_diagnostics if k not in f2_diagnostics}
    f2_only_documents = {k: f2_diagnostics[k] for k in f2_diagnostics if k not in f1_diagnostics}
    
    # First deal with shared documents.
    # We're looking for differences in the diagnostics.
    same_docs = []
    for doc in shared_documents:
        checksum_count = 0
        checksum_line_count = 0
        content_count = 0
        # If the set of diagnostics is different, examine the differences
        if f1_diagnostics[doc] != f2_diagnostics[doc]:
            print("Document {} has different diagnostics:".format(doc))
            # Look for the symmetric difference of the sets.
            # This is the set of elements that are in document one set but not the other.
            for diagnostic in f1_diagnostics[doc]:
                if diagnostic not in f2_diagnostics[doc]:
                    checksum = None
                    checksum_line = None
                    content = None
                    for potential_match in f2_diagnostics[doc]:    
                        # Check for checksum-only difference
                        if diagnostic["file"] == potential_match["file"] \
                            and diagnostic["line"] == potential_match["line"] \
                            and diagnostic["error"] == potential_match["error"]:
                                checksum = potential_match
                        # Check for checksum and line number-only difference
                        elif diagnostic["file"] == potential_match["file"] \
                            and diagnostic["error"] == potential_match["error"]:
                                if checksum_line is not None:
                                    if abs(int(diagnostic["line"]) - int(potential_match["line"])) \
                                    < abs(int(diagnostic["line"]) - int(checksum_line["line"])):
                                        checksum_line = potential_match
                                else:
                                    checksum_line = potential_match
                        # Check for content difference
                        elif diagnostic["file"] == potential_match["file"] \
                            and diagnostic["line"] == potential_match["line"]:
                                content = potential_match

                    if checksum is not None:
                        checksum_count += 1
                        # print("    Checksum-only difference:")
                        # print("    File {}: {}".format(file1, diagnostic["message"]))
                        # print("    File {}: {}".format(file2, checksum["message"]))
                    elif checksum_line is not None:
                        checksum_line_count += 1
                        # print("    Checksum and line number-only difference:")
                        # print("    File {}: {}".format(file1, diagnostic["message"]))
                        # print("    File {}: {}".format(file2, checksum_line["message"]))
                    elif content is not None:
                        content_count += 1
                        print("    Content difference:")
                        print("    File {}: {}".format(file1, diagnostic["message"]))
                        print("    File {}: {}".format(file2, content["message"]))
                    else:
                        print("    No match found for:")
                        print("    File {}: {}".format(file1, diagnostic["message"]))
            for diagnostic in f2_diagnostics[doc]:
                if diagnostic not in f1_diagnostics[doc]:
                    checksum = None
                    checksum_line = None
                    content = None
                    for potential_match in f1_diagnostics[doc]:    
                        # Check for checksum-only difference
                        if diagnostic["file"] == potential_match["file"] \
                            and diagnostic["line"] == potential_match["line"] \
                            and diagnostic["error"] == potential_match["error"]:
                                checksum = potential_match
                        # Check for checksum and line number-only difference
                        elif diagnostic["file"] == potential_match["file"] \
                            and diagnostic["error"] == potential_match["error"]:
                                if checksum_line is not None:
                                    if abs(int(diagnostic["line"]) - int(potential_match["line"])) \
                                    < abs(int(diagnostic["line"]) - int(checksum_line["line"])):
                                        checksum_line = potential_match
                                else:
                                    checksum_line = potential_match
                        # Check for content difference
                        elif diagnostic["file"] == potential_match["file"] \
                            and diagnostic["line"] == potential_match["line"]:
                                content = potential_match

                    if checksum is not None:
                        checksum_count += 1
                        # print("    Checksum-only difference:")
                        # print("    File {}: {}".format(file1, diagnostic["message"]))
                        # print("    File {}: {}".format(file2, checksum["message"]))
                    elif checksum_line is not None:
                        checksum_line_count += 1
                        # print("    Checksum and line number-only difference:")
                        # print("    File {}: {}".format(file1, diagnostic["message"]))
                        # print("    File {}: {}".format(file2, checksum_line["message"]))
                    elif content is not None:
                        content_count += 1
                        # print("    Content difference:")
                        # print("    File {}: {}".format(file1, diagnostic["message"]))
                        # print("    File {}: {}".format(file2, content["message"]))
                    else:
                        print("    No match found for:")
                        print("    File {}: {}".format(file1, diagnostic["message"]))
        
            print("    File {}: {} checksum-only changes".format(file1, checksum_count/2))
            print("    File {}: {} checksum and line number-only changes".format(file1, checksum_line_count/2))
        else:
            #print("Document {} has the same diagnostics".format(doc))
            same_docs.append(doc)
    
    if len(same_docs) > 0:
        print("<details>")
        print("<summary>Documents with identical diagnostics</summary>")
        print("```")
        for doc in same_docs:
            print("Document {} has the same diagnostics".format(doc))
        print("```")
        print("</details>")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare two TOML files")
    parser.add_argument("file1", help="First TOML file")
    parser.add_argument("file2", help="Second TOML file")
    args = parser.parse_args()
    compare_toml(args.file1, args.file2)