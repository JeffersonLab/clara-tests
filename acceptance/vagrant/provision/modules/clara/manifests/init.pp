class clara {
    include clara::java
    if $hostname =~ /^platform/ {
        include clara::webapp
    }
}
