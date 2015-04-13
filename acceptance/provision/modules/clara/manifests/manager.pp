class clara::manager {
    package { [
        "python-mock",
        "python-nose",
        "python-psutil",
        "python-colorama",
    ]:
        ensure => latest,
    }

    service { "clara-manager":
        ensure => "running",
        enable => "true",
        require => [ Package["python-zmq"], Package["python-psutil"] ]
    }

    file { "/etc/init/clara-manager.conf":
        mode => 600,
        owner => "root",
        group => "root",
        source => "puppet:///modules/clara/clara-manager.conf",
        notify => Service["clara-manager"],
    }
}
