class tools::vc {
    Package {
        ensure => installed,
    }

    package { [
        "git",
        "git-svn",
        "tig",
        "subversion",
    ]:
    }

    if $hostname =~ /^platform/ {
        package { "meld": }
    }

    File {
        ensure => present,
        owner  => "vagrant",
        group  => "vagrant",
    }

    file { "/home/vagrant/.config":
        ensure => "directory",
    }

    file { "/home/vagrant/.config/git":
        ensure => "directory",
    }

    file { "/home/vagrant/.config/git/config":
        source => "puppet:///modules/tools/git-config",
    }

    file { "/home/vagrant/.config/git/attributes":
        source => "puppet:///modules/tools/git-attributes",
    }

    file { "/home/vagrant/.config/git/ignore":
        source => "puppet:///modules/tools/git-ignore",
    }
}
