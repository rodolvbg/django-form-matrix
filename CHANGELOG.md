# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- The names of the columns were cut in the middle of a word ("Modific-ar")
  where the page around breaks words (django-unfold's wrappers), and ran
  into each other on narrow screens. Now their columns are never narrower
  than their names, a name never breaks inside a word, and a section too
  narrow for its columns scrolls sideways.

## [0.1.0] - 2026-10-17

### Added

- `MatrixField`, `MatrixWidget`, `Row` and `Column`: a table of rows and
  columns with a form field in every cell, optional collapsible sections and
  shortcuts to check a row, a column or a section.
- `django_form_matrix.contrib.permissions`: `PermissionMultipleChoiceField`,
  the permissions of an app/model/action in a matrix.
- Blocks in `matrix.html` and `permissions.html` (`section_summary`,
  `column_heading`, `cell`...) to extend them changing only a piece.
- `django_form_matrix.contrib.unfold.UnfoldMatrixMixin`: the matrix on
  django-unfold's palette (light and dark).
- Spanish translation.
