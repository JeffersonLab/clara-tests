class clara::webapp {
    Package {
        ensure => latest,
    }

    package { [
        "bundler",
    ]:
    }
}
