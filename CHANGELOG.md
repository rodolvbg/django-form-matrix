# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
