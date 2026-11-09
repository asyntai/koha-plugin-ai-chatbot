use Modern::Perl;
use FindBin;
use lib "$FindBin::Bin/..";

use Test::More;

# The plugin class needs Koha. Skip outside a Koha install. Run it there with
# PERL5LIB pointing at the Koha source.
eval { require Koha::Plugins::Base; 1 } or plan skip_all => 'Koha is not installed here';

my $class = 'Koha::Plugin::Com::Asyntai::AIAssistant';

use_ok($class);

is( $Koha::Plugin::Com::Asyntai::AIAssistant::metadata->{license}, 'GPL-3.0', 'plugin declares its license' );
is( $Koha::Plugin::Com::Asyntai::AIAssistant::metadata->{version}, $Koha::Plugin::Com::Asyntai::AIAssistant::VERSION, 'version in the metadata' );

ok( $class->can($_), "plugin has $_" ) for qw(install upgrade uninstall configure opac_js);
ok( !$class->can('intranet_js'), 'staff interface gets no chat' );

done_testing();
