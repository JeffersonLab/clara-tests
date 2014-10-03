class clara::manager {
    package { [
        "python-mock",
    ]:
        ensure => latest,
    }

    service { "clara-manager":
        ensure => "running",
        enable => "true",
    }

    file { "/etc/init/clara-manager.conf":
        mode => 600,
        owner => "root",
        group => "root",
        source => "puppet:///modules/clara/clara-manager.conf",
        notify => Service["clara-manager"],
    }
}
