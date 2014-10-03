class locales {
    package { "locales":
        ensure => latest,
    }
    file { "/var/lib/locales/supported.d/local":
        source  => "puppet:///modules/locales/local",
        mode    => 0644,
        ensure  => present,
        owner   => "root",
        group   => "root",
        require => Package[locales],
    }
    exec { "/usr/sbin/dpkg-reconfigure locales":
        subscribe => File["/var/lib/locales/supported.d/local"],
        refreshonly => true,
        require => File["/var/lib/locales/supported.d/local"],
    }
}
