use Modern::Perl;
use FindBin;
use lib "$FindBin::Bin/..";

use Test::More;

use Koha::Plugin::Com::Asyntai::AIAssistant::Settings;

my $settings = 'Koha::Plugin::Com::Asyntai::AIAssistant::Settings';
my $default  = $settings->DEFAULT_SCRIPT_URL;

is( $settings->read_widget_id('asyntai_ab12cd34'),       'asyntai_ab12cd34', 'bare ID' );
is( $settings->read_widget_id("  asyntai_ab12cd34 \n"),  'asyntai_ab12cd34', 'ID with spaces around it' );
is( $settings->read_widget_id(undef),                    q{},                'no value' );
is( $settings->read_widget_id(q{}),                      q{},                'empty value' );
is( $settings->read_widget_id('   '),                    q{},                'only spaces' );
is( $settings->read_widget_id('ab12cd34'),               q{},                'no prefix' );
is( $settings->read_widget_id('asyntai_ab12'),           q{},                'too short' );
is( $settings->read_widget_id( 'asyntai_' . 'a' x 65 ),  q{},                'too long' );
is( $settings->read_widget_id('asyntai_ab12cd34"><x>'),  q{},                'markup after the ID' );
is( $settings->read_widget_id("asyntai_ab12cd34\nabc"),  q{},                'second line after the ID' );
is( $settings->read_widget_id('asyntai_ab12cd34_more'),  q{},                'underscore inside the ID' );

my $snippet = '<script async src="https://widget.asyntai.com/static/js/chat-widget.js" data-asyntai-id="asyntai_ab12cd34"></script>';
is( $settings->read_widget_id($snippet), 'asyntai_ab12cd34', 'whole snippet' );

( my $single = $snippet ) =~ s/"/'/gxms;
is( $settings->read_widget_id($single), 'asyntai_ab12cd34', 'snippet with single quotes' );

( my $encoded = $snippet ) =~ s/"/&quot;/gxms;
is( $settings->read_widget_id($encoded), 'asyntai_ab12cd34', 'HTML encoded snippet' );

is( $settings->read_widget_id('<script data-asyntai-id="bad id"></script>'), q{}, 'snippet with a bad ID' );

is( $settings->read_script_url(undef),                          $default,                      'no address means the default' );
is( $settings->read_script_url('  '),                           $default,                      'spaces mean the default' );
is( $settings->read_script_url('https://cdn.example.org/w.js'), 'https://cdn.example.org/w.js', 'https address' );
is( $settings->read_script_url('HTTPS://cdn.example.org/w.js'), 'HTTPS://cdn.example.org/w.js', 'upper case scheme' );
is( $settings->read_script_url('http://cdn.example.org/w.js'),  q{},                           'http address' );
is( $settings->read_script_url('javascript:alert(1)'),          q{},                           'javascript address' );
is( $settings->read_script_url('https://a.org/"><script>'),     q{},                           'markup in the address' );
is( $settings->read_script_url('https://a.org/a b.js'),         q{},                           'space in the address' );

is(
    $settings->loader_tag( 'asyntai_ab12cd34', $default ),
    qq{<script async src="$default" data-asyntai-id="asyntai_ab12cd34"></script>},
    'tag matches the dashboard snippet'
);
is(
    $settings->loader_tag( 'asyntai_ab12cd34', $default, 'n0nce' ),
    qq{<script async src="$default" data-asyntai-id="asyntai_ab12cd34" nonce="n0nce"></script>},
    'tag carries a nonce'
);
is(
    $settings->loader_tag( 'asyntai_ab12cd34', 'https://a.org/w.js?a=1&b=2' ),
    '<script async src="https://a.org/w.js?a=1&amp;b=2" data-asyntai-id="asyntai_ab12cd34"></script>',
    'ampersand is escaped'
);

done_testing();
