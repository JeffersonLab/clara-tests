class clara {
    include clara::java
    include clara::cpp
    include clara::python
    if $hostname =~ /^platform/ {
        include clara::webapp
    }
    include clara::manager
}
