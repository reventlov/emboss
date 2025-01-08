# Design of the Emboss Tool

This document describes the internals of Emboss.  End users do not need to read
this document.

## Overall Design

The Emboss compiler follows a reasonably standard compiler design, where the
input source text is first converted to an *intermediate representation* (IR),
then various operations are performed on the IR, and finally the IR is used to
construct the final output — at the time of writing, C++ source code:

```mermaid
%%{init: {"flowchart": {"htmlLabels": false}} }%%
graph LR;
    diskstart@{ shape: doc, label: "example.emb" }
    parser["Parser"]
    processing@{ shape: procs, label: "IR processing" }
    backend["C++ Code Generator"]
    diskend@{ shape: doc, label: "example.emb.h" }
    diskstart-- ".emb" -->parser
    parser-- IR -->processing
    processing-- IR -->backend
    backend-- "C++" -->diskend
```

Currently, Emboss is split into two programs: the *front end*, which parses the
input and does almost all of the IR processing, and the *C++ back end*, which
does a minimal amount of C++-specific IR processing and generates the final C++
code.  This split makes it straightforward to add new back ends later:

```mermaid
%%{init: {"flowchart": {"htmlLabels": false}} }%%
graph LR;
    diskstart@{ shape: doc, label: "example.emb" }
    parser["Parser"]
    processing@{ shape: procs, label: "IR processing" }
    cppbackend["C++ Code Generator"]
    cppdiskend@{ shape: doc, label: "example.emb.h" }
    rustbackend["Rust Code Generator"]
    rustdiskend@{ shape: doc, label: "example.emb.rs" }
    mdbackend["Documentation Generator"]
    mddiskend@{ shape: doc, label: "example.emb.md" }
    diskstart-- ".emb" -->parser
    parser-- IR -->processing
    processing-- IR -->cppbackend
    cppbackend-- "C++" -->cppdiskend
    processing-- IR -->rustbackend
    rustbackend-- Rust -->rustdiskend
    processing-- IR -->mdbackend
    mdbackend-- Markdown -->mddiskend
```


### IR

Most of the Emboss compiler operates on a data structure known as an *IR*, or
intermediate representation.  The Emboss IR is a tree, with node types defined
in [compiler/util/ir_data.py][ir_data_py].

[ir_data_py]: ../compiler/util/ir_data.py

The first stage of the compiler — the parser — generates an "initial" IR, which
only contains information that is directly available in the source tree:

```mermaid
digraph TD:
  n0@{ shape=diamond, label="module" }
  n0 --> n1
  n0 --> n6
  n0 --> n59
  n0 --> n61
  n0 --> l34
  n1@{ shape=diamond, label="attributes" }
  n1 --> n2
  n1 --> n4
  n2@{ shape=diamond, label="attribute" }
  n2 --> l0
  n2 --> n3
  n2 --> l2
  n3@{ shape=diamond, label="value" }
  n3 --> l1
  n4@{ shape=diamond, label="attribute" }
  n4 --> l3
  n4 --> n5
  n4 --> l5
  n4 --> l6
  n5@{ shape=diamond, label="value" }
  n5 --> l4
  n6@{ shape=diamond, label="types" }
  n6 --> n7
  n7@{ shape=diamond, label="type" }
  n7 --> n8
  n7 --> l29
  n7 --> n58
  n8@{ shape=diamond, label="structure" }
  n8 --> n9
  n9@{ shape=diamond, label="fields" }
  n9 --> n10
  n9 --> n21
  n9 --> n36
  n9 --> n47
  n10@{ shape=diamond, label="field" }
  n10 --> n11
  n10 --> n14
  n10 --> n19
  n10 --> n20
  n11@{ shape=diamond, label="location" }
  n11 --> n12
  n11 --> n13
  n12@{ shape=diamond, label="start" }
  n12 --> l7
  n13@{ shape=diamond, label="size" }
  n13 --> l8
  n14@{ shape=diamond, label="type" }
  n14 --> n15
  n15@{ shape=diamond, label="atomic_type" }
  n15 --> n16
  n16@{ shape=diamond, label="reference" }
  n16 --> n17
  n17@{ shape=diamond, label="source_names" }
  n17 --> n18
  n18@{ shape=diamond, label="source_name" }
  n18 --> l9
  n19@{ shape=diamond, label="name" }
  n19 --> l10
  n20@{ shape=diamond, label="existence_condition" }
  n20 --> l11
  n21@{ shape=diamond, label="field" }
  n21 --> n22
  n21 --> n25
  n21 --> n34
  n21 --> n35
  n22@{ shape=diamond, label="location" }
  n22 --> n23
  n22 --> n24
  n23@{ shape=diamond, label="start" }
  n23 --> l12
  n24@{ shape=diamond, label="size" }
  n24 --> l13
  n25@{ shape=diamond, label="type" }
  n25 --> n26
  n26@{ shape=diamond, label="array_type" }
  n26 --> n27
  n26 --> n33
  n27@{ shape=diamond, label="base_type" }
  n27 --> n28
  n27 --> n32
  n28@{ shape=diamond, label="atomic_type" }
  n28 --> n29
  n29@{ shape=diamond, label="reference" }
  n29 --> n30
  n30@{ shape=diamond, label="source_names" }
  n30 --> n31
  n31@{ shape=diamond, label="source_name" }
  n31 --> l14
  n32@{ shape=diamond, label="size_in_bits" }
  n32 --> l15
  n33@{ shape=diamond, label="element_count" }
  n33 --> l16
  n34@{ shape=diamond, label="name" }
  n34 --> l17
  n35@{ shape=diamond, label="existence_condition" }
  n35 --> l18
  n36@{ shape=diamond, label="field" }
  n36 --> n37
  n36 --> n40
  n36 --> n45
  n36 --> n46
  n37@{ shape=diamond, label="location" }
  n37 --> n38
  n37 --> n39
  n38@{ shape=diamond, label="start" }
  n38 --> l19
  n39@{ shape=diamond, label="size" }
  n39 --> l20
  n40@{ shape=diamond, label="type" }
  n40 --> n41
  n41@{ shape=diamond, label="atomic_type" }
  n41 --> n42
  n42@{ shape=diamond, label="reference" }
  n42 --> n43
  n43@{ shape=diamond, label="source_names" }
  n43 --> n44
  n44@{ shape=diamond, label="source_name" }
  n44 --> l21
  n45@{ shape=diamond, label="name" }
  n45 --> l22
  n46@{ shape=diamond, label="existence_condition" }
  n46 --> l23
  n47@{ shape=diamond, label="field" }
  n47 --> n48
  n47 --> n51
  n47 --> n56
  n47 --> n57
  n48@{ shape=diamond, label="location" }
  n48 --> n49
  n48 --> n50
  n49@{ shape=diamond, label="start" }
  n49 --> l24
  n50@{ shape=diamond, label="size" }
  n50 --> l25
  n51@{ shape=diamond, label="type" }
  n51 --> n52
  n52@{ shape=diamond, label="atomic_type" }
  n52 --> n53
  n53@{ shape=diamond, label="reference" }
  n53 --> n54
  n54@{ shape=diamond, label="source_names" }
  n54 --> n55
  n55@{ shape=diamond, label="source_name" }
  n55 --> l26
  n56@{ shape=diamond, label="name" }
  n56 --> l27
  n57@{ shape=diamond, label="existence_condition" }
  n57 --> l28
  n58@{ shape=diamond, label="name" }
  n58 --> l30
  n59@{ shape=diamond, label="documentations" }
  n59 --> n60
  n60@{ shape=diamond, label="documentation" }
  n60 --> l31
  n61@{ shape=diamond, label="foreign_imports" }
  n61 --> n62
  n62@{ shape=diamond, label="foreign_import" }
  n62 --> l32
  n62 --> l33
  l0@{ shape=box, label="name: byte_order" }
  l1@{ shape=box, label="string_constant: LittleEndian" }
  l2@{ shape=box, label="is_default: True" }
  l3@{ shape=box, label="name: namespace" }
  l4@{ shape=box, label="string_constant: emboss::test" }
  l5@{ shape=box, label="is_default: False" }
  l6@{ shape=box, label="back_end: cpp" }
  l7@{ shape=box, label="constant: 0" }
  l8@{ shape=box, label="constant: 4" }
  l9@{ shape=box, label="text: UInt" }
  l10@{ shape=box, label="name: file_state" }
  l11@{ shape=box, label="boolean_constant: True" }
  l12@{ shape=box, label="constant: 4" }
  l13@{ shape=box, label="constant: 12" }
  l14@{ shape=box, label="text: UInt" }
  l15@{ shape=box, label="constant: 8" }
  l16@{ shape=box, label="constant: 12" }
  l17@{ shape=box, label="name: file_name" }
  l18@{ shape=box, label="boolean_constant: True" }
  l19@{ shape=box, label="constant: 16" }
  l20@{ shape=box, label="constant: 4" }
  l21@{ shape=box, label="text: UInt" }
  l22@{ shape=box, label="name: file_size_kb" }
  l23@{ shape=box, label="boolean_constant: True" }
  l24@{ shape=box, label="constant: 20" }
  l25@{ shape=box, label="constant: 4" }
  l26@{ shape=box, label="text: UInt" }
  l27@{ shape=box, label="name: media" }
  l28@{ shape=box, label="boolean_constant: True" }
  l29@{ shape=box, label="addressable_unit: 8" }
  l30@{ shape=box, label="name: LogFileStatus" }
  l31@{ shape=box, label="text: This is a simple, re" }
  l32@{ shape=box, label="file_name: " }
  l33@{ shape=box, label="local_name: " }
  l34@{ shape=box, label="source_text: # Copyright 2019 Goo" }
```


The back ends read the IR and emit code to view and manipulate Emboss-defined
data structures.  Currently, only a C++ back end exists.

Implementation note: for efficiency, the standalone [`embossc`][embossc_source] driver just imports the front end and C++ back end directly

## Front End

*Implemented in [compiler/front_end/...][front_end]*

[front_end]: compiler/front_end/

The front end is responsible for reading in Emboss definitions and producing a
normalized intermediate representation (IR).  It is divided into several steps:
roughly, parsing, import resolution, symbol resolution, and validation.

The front end is orchestrated by [glue.py][glue_py], which runs each front end
component in the proper order to construct an IR suitable for consumption by the
back end.

[glue_py]: front_end/glue.py

The actual driver program is [emboss_front_end.py][emboss_front_end_py], which
just calls `glue.ParseEmbossFile` and prints the results.

[emboss_front_end_py]: front_end/emboss_front_end.py

### File Parsing

Per-file parsing consumes the text of a single Emboss module, and produces an
"undecorated" IR for the module, containing only syntactic-level information
from the module.

This "undecorated" IR is (almost) a subset of the final IR: later steps will add
information and perform validation, but will rarely remove anything from the IR
before it is emitted.

#### Tokenization

*Implemented in [tokenizer.py][tokenizer_py]*

[tokenizer_py]: front_end/tokenizer.py

The tokenizer is a fairly standard tokenizer, with Indent/Dedent insertion a la
Python.  It divides source text into `parse_types.Symbol` objects, suitable for
feeding into the parser.

#### Syntax Tree Generation

*Implemented in [lr1.py][lr1_py] and [parser_generator.py][parser_generator_py], with a fa&ccedil;ade in [structure_parser.py][structure_parser_py]*

[lr1_py]: front_end/lr1.py
[parser_generator_py]: front_end/parser_generator.py
[structure_parser_py]: front_end/structure_parser.py

Emboss uses a pretty standard Shift-Reduce LR(1) parser.  This is implemented in
three parts in Emboss:

* A generic parser generator implementing the table generation algorithms from
  *[Compilers: Principles, Techniques, & Tools][dragon_book]* and the
  error-marking algorithm from *[Generating LR Syntax Error Messages from
  Examples][jeffery_2003]*.
* An Emboss-specific parser builder which glues the Emboss tokenizer, grammar,
  and error examples to the parser generator, producing an Emboss parser.
* The Emboss grammar, which is extracted from the file normalizer
  (*[module_ir.py][module_ir_py]*).

[dragon_book]: http://www.amazon.com/Compilers-Principles-Techniques-Tools-2nd/dp/0321486811
[jeffery_2003]: http://dl.acm.org/citation.cfm?id=937566

#### Normalization

*Implemented in [module_ir.py][module_ir_py]*

[module_ir_py]: front_end/module_ir.py

Once a parse tree has been generated, it is fed into a normalizer which
recursively turns the raw syntax tree into a "first stage" intermediate
representation (IR).  The first stage IR serves to isolate later stages from
minor changes in the grammar, but only contains information from a single file,
and does not perform any semantic checking.

### Import Resolution

*TODO(bolms): Implement imports.*

After each file is parsed, any new imports it has are added to a work queue.
Each file in the work queue is parsed, potentially adding more imports to the
queue, until the queue is empty.

### Symbol Resolution

*Implemented in [symbol_resolver.py][symbol_resolver_py]*

[symbol_resolver_py]: front_end/symbol_resolver.py

Symbol resolution is the process of correlating names in the IR.  At the end of
symbol resolution, every named entity (type definition, field definition, enum
name, etc.) has a `CanonicalName`, and every reference in the IR has a
`Reference` to the entity to which it refers.

This assignment occurs in two passes.  First, the full IR is scanned, generating
scoped symbol tables (nested dictionaries of names to `CanonicalName`), and
assigning identities to each `Name` in the IR.  Then the IR is fully scanned a
second time, and each `Reference` in the IR is resolved: all scopes visible to
the reference are scanned for the name, and the corresponding `CanonicalName` is
assigned to the reference.

### Validation

*TODO(bolms): other validations?*

#### Size Checking

*TODO(bolms): describe*

#### Overlap Checking

*TODO(bolms): describe*

## Back End

*Implemented in [back_end/...][back_end]*

[back_end]: back_end/

Currently, only a C++ back end is implemented.

A back end takes Emboss IR and produces code in a specific language for
manipulating the Emboss-defined data structures.

### C++

*Implemented in [header_generator.py][header_generator_py] with templates in
[generated_code_templates][generated_code_templates], support code in
[emboss_cpp_util.h][emboss_cpp_util_h], and a driver program in
[emboss_codegen_cpp.py][emboss_codegen_cpp_py]*

[header_generator_py]: back_end/cpp/header_generator.py
[generated_code_templates]: back_end/cpp/generated_code_templates
[emboss_cpp_util_h]: back_end/cpp/emboss_cpp_util.h
[emboss_codegen_cpp_py]: back_end/cpp/emboss_codegen_cpp.py

The C++ code generator is currently very minimal.  `header_generator.py`
essentially inserts values from the IR into text templates.

*TODO(bolms): add more documentation once the C++ back end has more features.*
