class common {
    $private_ip = $hostname ? {
        'platform' => '10.11.1.100',
        'dpe1'     => '10.11.1.101',
        'dpe2'     => '10.11.1.102',
    }

    # Fix "localhost" IP in Java
    host {
        $hostname: ip => $private_ip
    }

    file { [
        "/home/vagrant/clara",
        "/vagrant/acceptance/services",
        "/vagrant/acceptance/services/log",
    ]:
        ensure => "directory",
        owner => "vagrant",
        group => "vagrant",
    }

    file { "/home/vagrant/clara/services":
        ensure => "link",
        target => "/vagrant/acceptance/services",
        force  => "true",
    }
}

include common
include locales
include tools
include clara
