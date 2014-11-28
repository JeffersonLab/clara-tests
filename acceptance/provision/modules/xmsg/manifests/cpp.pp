class xmsg::cpp {
    Package {
        ensure => latest,
    }

    package { [
        "build-essential",
        "g++",
        "cmake",
    ]:
    }

    package { [
        "libzmq3-dev",
        "libprotobuf-dev",
        "protobuf-compiler",
    ]:
    }
}
