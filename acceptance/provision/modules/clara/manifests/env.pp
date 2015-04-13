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

    file { "/home/vagrant/bin/clara-testing":
        source => "puppet:///modules/clara/clara-testing",
    }

    file {'gradle.userhome':
        path   => "/home/vagrant/.gradle",
        ensure => "directory",
        owner  => "vagrant",
        group  => "vagrant",
    }

    file {'gradle.properties':
        path    => "/home/vagrant/.gradle/gradle.properties",
        ensure  => "present",
        owner   => "vagrant",
        group   => "vagrant",
        content => "org.gradle.daemon=true",
    }

    file {'gradle.sh':
      path    => '/etc/profile.d/gradle.sh',
      ensure  => present,
      mode    => 755,
      content => 'export PATH=/vagrant/acceptance/provision/gradle:$PATH'
    }
}
