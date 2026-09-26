# Plugin development

Plugins should implement the interfaces in
`signal_processing_toolkit.core.plugins.interface`, declare their optional
dependencies, and avoid importing GUI or hardware libraries at module import
time. Register plugins through the existing manager, validate configuration,
provide a close/reset lifecycle, and add an isolated test. Plugins must not
mutate shared signal arrays and should preserve signal metadata and provenance.
