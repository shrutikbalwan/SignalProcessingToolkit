# Architecture guide

The package is layered: validated models and DSP algorithms form the mandatory
core; streaming and acquisition add bounded state and timestamps; UI and
optional hardware/audio/image/AI integrations are isolated adapters. See
the repository `ARCHITECTURE.md` file for the component map and the ADR pages
in this documentation for durable decisions.
