# Hackolade Studio CLI for this repository's CI (spec 0006, D9).
#
# Built on Hackolade's ready-made CLI image, which bundles every target plugin at
# the versions fixed by its tag (https://github.com/hackolade/docker/tree/main/Studio).
# Pin the tag: Hackolade publishes no "latest". ci/plugins.txt lists the plugins
# this repository needs and their minimum versions; CI checks them on every run.
#
# Build from the repository root:  docker build -f ci/Dockerfile -t edm-hck-cli .
# The licence is never baked in: CI validates the HACKOLADE_LICENSE secret at run time.

# Studio 8.13.0 or later (supertype groups, D9). Check the tag exists on
# https://hub.docker.com/r/hackolade/hck-cli/tags before changing it.
ARG HCK_CLI_TAG=8.13.0
FROM hackolade/hck-cli:${HCK_CLI_TAG}

# The repository's Hackolade settings: EDM custom properties and naming files.
# Same layout as `make hackolade-config` installs on a workstation. Spike T5
# confirms the CLI reads them from here.
COPY --chown=1000:1001 hackolade/customProperties/Polyglot/ /home/hackolade/.hackolade/options/Polyglot/customProperties/
COPY --chown=1000:1001 hackolade/customProperties/PostgreSQL/ /home/hackolade/.hackolade/options/PostgreSQL/customProperties/
COPY --chown=1000:1001 hackolade/naming/ /home/hackolade/.hackolade/options/naming/
