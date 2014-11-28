class xmsg::java {
    Package {
        ensure => latest,
    }

    package { [
        "openjdk-7-jdk",
        "ant",
    ]:
    }
}
