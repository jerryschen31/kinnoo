## Feature12 Review (Jerry)

- feature12 implements kinnoo publish as publishing to a local registry at ~/.kinnoo/
- this feature will largely be deprecated
- instead, kinnoo publish will publish to a remote registry. For now, we will mock a registry on the local filesystem as registry-scratch/...
- kinnoo pack will be refactored into a command that packs an agent to a local archive ~/.kinnoo/archive/
- these refactors will be implemented as feature13