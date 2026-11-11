# Research dataset workspace

Place an authorized C-NMC 2019 copy under this directory only after reviewing the dataset terms, attribution rules, and institutional approval requirements. The repository does not download or contain the dataset.

The training manifest is a CSV with these columns:

~~~text
image_path,label,subject_id
~~~

Paths are relative to the configured image root. Use the source dataset's subject keys only to create subject-disjoint partitions. Do not add patient names or other direct identifiers. Review the original dataset documentation for its intended labels and permitted use before constructing the manifest.

Generated manifests, images, cached data, and labels are ignored by Git. A header-only example is available as manifest.example.csv.
