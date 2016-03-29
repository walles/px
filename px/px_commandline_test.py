import px_commandline


def test_get_command_python():
    assert px_commandline.get_command("python") == "python"
    assert px_commandline.get_command("/apa/Python") == "Python"
    assert px_commandline.get_command("python --help") == "python"

    # These are inspired by Python 2.7.11 --help output
    assert px_commandline.get_command("python apa.py") == "apa.py"
    assert px_commandline.get_command("python /usr/bin/apa.py") == "apa.py"
    assert px_commandline.get_command("python2.7 /usr/bin/apa.py") == "apa.py"
    assert px_commandline.get_command("python /usr/bin/hej") == "hej"
    assert px_commandline.get_command("python /usr/bin/hej gris --flaska") == "hej"
    assert px_commandline.get_command("python -c cmd") == "python"
    assert px_commandline.get_command("python -m mod") == "mod"
    assert px_commandline.get_command("python -m mod --hej gris --frukt") == "mod"
    assert px_commandline.get_command("Python -") == "Python"

    # To begin with, any switches other than -c -m or - and we give up. Room for
    # future improvement.
    assert px_commandline.get_command("python -W warning:spec apa.py") == "python"
    assert px_commandline.get_command("python -u -t -m mod") == "python"

    # Invalid command lines
    assert px_commandline.get_command("python -W") == "python"
    assert px_commandline.get_command("python -c") == "python"
    assert px_commandline.get_command("python -m") == "python"
    assert px_commandline.get_command("python -m   ") == "python"
    assert px_commandline.get_command("python -m -u") == "python"
    assert px_commandline.get_command("python    ") == "python"


def test_get_command_java():
    assert px_commandline.get_command("java") == "java"
    assert px_commandline.get_command("java -version") == "java"
    assert px_commandline.get_command("java -help") == "java"

    assert px_commandline.get_command("java SomeClass") == "SomeClass"
    assert px_commandline.get_command("java x.y.SomeClass") == "SomeClass"
    assert px_commandline.get_command("java -jar flaska.jar") == "flaska.jar"
    assert px_commandline.get_command("java -jar /a/b/flaska.jar") == "flaska.jar"

    # We should ignore certain command line parameters
    assert px_commandline.get_command("java -server SomeClass") == "SomeClass"
    assert px_commandline.get_command("java -Xwhatever SomeClass") == "SomeClass"
    assert px_commandline.get_command("java -Dwhatever SomeClass") == "SomeClass"
    assert px_commandline.get_command("java -cp /a/b/c SomeClass") == "SomeClass"
    assert px_commandline.get_command("java -classpath /a/b/c SomeClass") == "SomeClass"

    # Tests for invalid command lines
    assert px_commandline.get_command("java -cp /a/b/c") == "java"
    assert px_commandline.get_command("java  ") == "java"
    assert px_commandline.get_command("java -jar") == "java"
    assert px_commandline.get_command("java -jar    ") == "java"

    # FIXME: Add test for classpath containing spaces? I say this should be
    # postponed until we have a real world use case for that.
    pass


def test_get_command_java_gradled():
    commandline = (
        "/Library/Java/JavaVirtualMachines/jdk1.8.0_60.jdk/Contents/Home/bin/java " +
        "-XX:MaxPermSize=256m -XX:+HeapDumpOnOutOfMemoryError -Xmx1024m " +
        "-Dfile.encoding=UTF-8 -Duser.country=SE -Duser.language=sv -Duser.variant -cp " +
        "/Users/johan/.gradle/wrapper/dists/gradle-2.8-all/gradle-2.8/lib/gradle-launcher-2.8.jar" +
        " org.gradle.launcher.daemon.bootstrap.GradleDaemon 2.8")
    assert px_commandline.get_command(commandline) == "GradleDaemon"


def test_get_command_java_teamcity():
    # FIXME: Get an example TeamCity command line here
    assert False


def test_get_command_java_logstash():
    # FIXME: Get an example logstash command line here
    assert False


def test_get_command_java_jar():
    # FIXME: Get an example java -jar command line here
    assert False
