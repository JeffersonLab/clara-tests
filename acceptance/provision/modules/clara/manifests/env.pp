class clara::env {
    File {
        ensure => present,
        owner => "vagrant",
        group => "vagrant",
    }

    file { [
        "/home/vagrant/clara",
        "/vagrant/acceptance/services",
        "/vagrant/acceptance/services/log",
    ]:
        ensure => "directory",
    }

    file { "/home/vagrant/clara/services":
        ensure => "link",
        target => "/vagrant/acceptance/services",
        force  => "true",
    }
}
